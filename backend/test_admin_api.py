import os
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite:///./test_admin.db"
Path("test_admin.db").unlink(missing_ok=True)

from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.main import app
from app.models.content import Post, PostStatus
from app.models.user import User, UserRole


def register(client: TestClient, phone: str, nickname: str) -> tuple[int, dict[str, str]]:
    response = client.post(
        "/api/auth/register",
        json={"phone": phone, "password": "AdminTest123", "nickname": nickname},
    )
    data = response.json()["data"]
    return data["user_id"], {"Authorization": f"Bearer {data['token']}"}


def run() -> None:
    with TestClient(app) as client:
        admin_id, admin_headers = register(client, "13800006001", "Admin")
        user_id, user_headers = register(client, "13800006002", "ReportedUser")
        db = SessionLocal()
        admin = db.query(User).filter(User.id == admin_id).first()
        admin.role = UserRole.ADMIN
        db.commit()
        db.close()

        category_id = client.get("/api/categories").json()["data"][0]["id"]
        created = client.post(
            "/api/posts",
            headers=user_headers,
            json={"category_id": category_id, "title": "待审核帖子", "content": "需要管理员处理"},
        )
        post_id = created.json()["data"]["id"]
        db = SessionLocal()
        db.query(Post).filter(Post.id == post_id).update({"status": PostStatus.REVIEWING})
        db.commit()
        db.close()

        report = client.post(
            "/api/report",
            headers=admin_headers,
            json={"target_type": "user", "target_id": user_id, "reason": "spam", "description": "测试举报"},
        )
        assert report.status_code == 201, report.text
        report_id = report.json()["data"]["id"]

        queue = client.get("/api/admin/review-queue", headers=admin_headers)
        assert queue.status_code == 200 and queue.json()["data"]["total"] == 1
        review_id = queue.json()["data"]["items"][0]["id"]
        reviewed = client.post(
            f"/api/admin/review-queue/{review_id}/review",
            headers=admin_headers,
            json={"action": "approve"},
        )
        assert reviewed.status_code == 200 and reviewed.json()["data"]["status"] == "published"

        users = client.get("/api/admin/users", headers=admin_headers)
        assert users.status_code == 200 and users.json()["data"]["total"] == 2
        banned = client.post(
            f"/api/admin/users/{user_id}/ban",
            headers=admin_headers,
            json={"action": "ban", "reason": "违规", "duration_hours": 24},
        )
        assert banned.status_code == 200 and banned.json()["data"]["status"] == "disabled"
        unbanned = client.post(
            f"/api/admin/users/{user_id}/ban", headers=admin_headers, json={"action": "unban"}
        )
        assert unbanned.json()["data"]["status"] == "active"

        reports = client.get("/api/admin/reports", headers=admin_headers)
        assert reports.status_code == 200 and reports.json()["data"]["total"] == 1
        handled = client.post(
            f"/api/admin/reports/{report_id}",
            headers=admin_headers,
            json={"action": "resolve", "comment": "已处理"},
        )
        assert handled.json()["data"]["status"] == "resolved"

        category = client.post(
            "/api/admin/categories",
            headers=admin_headers,
            json={"name": "管理测试", "description": "测试板块"},
        )
        assert category.status_code == 201
        word = client.post(
            "/api/admin/sensitive-words",
            headers=admin_headers,
            json={"word": "违规广告", "level": "review"},
        )
        assert word.status_code == 201
        assert len(client.get("/api/admin/sensitive-words", headers=admin_headers).json()["data"]) == 1

        stats = client.get("/api/admin/stats/overview", headers=admin_headers)
        assert stats.status_code == 200 and stats.json()["data"]["total_posts"] == 1
        trend = client.get("/api/admin/stats/trend", headers=admin_headers)
        assert trend.status_code == 200 and len(trend.json()["data"]["content_stats"]) == 7
        logs = client.get("/api/admin/activity-logs", headers=admin_headers)
        assert logs.status_code == 200 and logs.json()["data"]["total"] >= 1

        assert client.get("/api/admin/users", headers=user_headers).status_code == 403


if __name__ == "__main__":
    try:
        run()
        print("admin API tests passed")
    finally:
        Path("test_admin.db").unlink(missing_ok=True)
