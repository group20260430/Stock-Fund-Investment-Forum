import os
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite:///./test_content.db"
Path("test_content.db").unlink(missing_ok=True)

from fastapi.testclient import TestClient

from app.main import app


def run() -> None:
    with TestClient(app) as client:
        registered = client.post(
            "/api/auth/register",
            json={"phone": "13800001001", "password": "Content123", "nickname": "content_user"},
        )
        assert registered.status_code == 201, registered.text
        token = registered.json()["data"]["token"]
        headers = {"Authorization": f"Bearer {token}"}

        categories = client.get("/api/categories")
        assert categories.status_code == 200, categories.text
        category_id = categories.json()["data"][0]["id"]

        created = client.post(
            "/api/posts",
            headers=headers,
            json={
                "category_id": category_id,
                "title": "内容系统测试帖",
                "content": "这是一篇真实写入数据库的测试帖。",
                "post_type": "poll",
                "tags": ["测试", "API"],
                "attachments": [
                    {
                        "file_name": "report.pdf",
                        "file_url": "https://example.com/report.pdf",
                        "file_size": 1024,
                        "file_type": "application/pdf",
                    }
                ],
                "vote_options": [{"label": "看多"}, {"label": "看空"}],
            },
        )
        assert created.status_code == 201, created.text
        post_id = created.json()["data"]["id"]

        listing = client.get("/api/posts", params={"keyword": "测试"})
        assert listing.status_code == 200
        assert listing.json()["data"]["total"] == 1

        detail = client.get(f"/api/posts/{post_id}")
        assert detail.status_code == 200, detail.text
        post = detail.json()["data"]
        assert post["attachments"][0]["file_name"] == "report.pdf"
        option_id = post["vote_options"][0]["id"]

        voted = client.post(
            f"/api/posts/{post_id}/vote",
            headers=headers,
            json={"option_ids": [option_id]},
        )
        assert voted.status_code == 200, voted.text
        assert voted.json()["data"]["results"][0]["vote_count"] == 1

        updated = client.put(
            f"/api/posts/{post_id}",
            headers=headers,
            json={
                "category_id": category_id,
                "title": "已编辑的帖子",
                "content": "更新后的内容",
                "post_type": "normal",
                "tags": [],
            },
        )
        assert updated.status_code == 200, updated.text

        deleted = client.delete(f"/api/posts/{post_id}", headers=headers)
        assert deleted.status_code == 204, deleted.text
        assert client.get(f"/api/posts/{post_id}").status_code == 404


if __name__ == "__main__":
    try:
        run()
        print("content API tests passed")
    finally:
        Path("test_content.db").unlink(missing_ok=True)
