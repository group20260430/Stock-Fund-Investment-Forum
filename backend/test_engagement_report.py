import gc
import os
import pathlib
import sys
import time

os.environ["DATABASE_URL"] = "sqlite:///./test_engagement_report.db"

DB_PATH = pathlib.Path("test_engagement_report.db")
DB_PATH.unlink(missing_ok=True)

import app.models  # noqa: F401
from fastapi.testclient import TestClient

from app.db.session import SessionLocal, engine
from app.main import app
from app.models.user import User, UserRole

passed = 0
failed = 0


def emit(text: str) -> None:
    sys.stdout.buffer.write(f"{text}\n".encode("utf-8", errors="replace"))


def check(label: str, expect: int, response):
    global passed, failed
    body = response.json()
    ok = response.status_code == expect
    if ok:
        passed += 1
        marker = "OK"
    else:
        failed += 1
        marker = "FAIL"
    message = body.get("message", body.get("detail", ""))
    emit(f"{marker} | {label}: HTTP {response.status_code} | {message}")
    if not ok:
        emit(f"     EXPECTED {expect}, GOT {response.status_code}")
        emit(f"     Full response: {body}")
    return ok, body


def register_user(client: TestClient, phone: str, nickname: str) -> dict[str, object]:
    response = client.post(
        "/api/auth/register",
        json={"phone": phone, "password": "Engagement123", "nickname": nickname},
    )
    ok, body = check(f"register {nickname}", 201, response)
    if not ok:
        raise RuntimeError(f"failed to register {nickname}")
    token = body["data"]["token"]
    return {
        "user_id": body["data"]["user_id"],
        "headers": {"Authorization": f"Bearer {token}"},
    }


def promote_admin(user_id: int) -> None:
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.id == user_id).first()
        admin.role = UserRole.ADMIN
        db.commit()
    finally:
        db.close()


def first_category_id(client: TestClient) -> int:
    response = client.get("/api/categories")
    ok, body = check("categories", 200, response)
    if not ok:
        raise RuntimeError("failed to load categories")
    return body["data"][0]["id"]


def create_post(client: TestClient, headers: dict[str, str], category_id: int, title: str, content: str):
    return client.post(
        "/api/posts",
        headers=headers,
        json={
            "category_id": category_id,
            "title": title,
            "content": content,
            "post_type": "normal",
            "status": "published",
            "tags": ["engagement"],
            "attachments": [],
            "vote_options": [],
        },
    )


def create_comment(client: TestClient, headers: dict[str, str], post_id: int, content: str):
    return client.post(
        f"/api/posts/{post_id}/comments",
        headers=headers,
        json={"content": content},
    )


def like_post(client: TestClient, headers: dict[str, str], post_id: int):
    return client.post(f"/api/posts/{post_id}/like", headers=headers)


def expect_keys(label: str, data: dict, keys: list[str]) -> None:
    global passed, failed
    missing = [key for key in keys if key not in data]
    if missing:
        failed += 1
        emit(f"FAIL | {label}: missing keys {missing}")
        return
    passed += 1
    emit(f"OK | {label}: keys present")


def run() -> None:
    with TestClient(app) as client:
        admin = register_user(client, "13800008101", "eng_admin")
        author = register_user(client, "13800008102", "eng_author")
        liker = register_user(client, "13800008103", "eng_liker")

        promote_admin(admin["user_id"])

        empty_response = client.get(
            "/api/admin/stats/engagement",
            headers=admin["headers"],
        )
        ok, body = check("engagement empty", 200, empty_response)
        if ok:
            data = body["data"]
            expect_keys(
                "engagement empty fields",
                data,
                ["overview", "daily_breakdown", "top_contributors", "engagement_distribution"],
            )

        no_auth_response = client.get("/api/admin/stats/engagement")
        check("engagement no auth", 403, no_auth_response)

        user_response = client.get(
            "/api/admin/stats/engagement",
            headers=author["headers"],
        )
        check("engagement non admin", 403, user_response)

        category_id = first_category_id(client)
        created = create_post(
            client,
            author["headers"],
            category_id,
            "用户参与度统计测试帖子",
            "这是一篇用于验证参与度报告接口的测试帖子，长度足够用于正常发布。",
        )
        ok, body = check("engagement setup post", 201, created)
        if not ok:
            return
        post_id = body["data"]["id"]

        comment = create_comment(
            client,
            author["headers"],
            post_id,
            "这是一条用于生成评论统计的测试评论内容。",
        )
        check("engagement setup comment", 201, comment)

        like = like_post(client, liker["headers"], post_id)
        check("engagement setup like", 200, like)

        populated_response = client.get(
            "/api/admin/stats/engagement?period=weekly",
            headers=admin["headers"],
        )
        ok, body = check("engagement populated", 200, populated_response)
        if ok:
            data = body["data"]
            overview = data["overview"]
            expect_keys(
                "engagement populated fields",
                data,
                ["overview", "daily_breakdown", "top_contributors", "engagement_distribution"],
            )
            if overview["active_users"] >= 2 and overview["total_posts"] >= 1 and overview["total_comments"] >= 1:
                globals()["passed"] += 1
                emit("OK | engagement populated overview: counts updated")
            else:
                globals()["failed"] += 1
                emit(f"FAIL | engagement populated overview: {overview}")
            if data["top_contributors"]:
                globals()["passed"] += 1
                emit("OK | engagement populated contributors: non-empty")
            else:
                globals()["failed"] += 1
                emit("FAIL | engagement populated contributors: empty")


def _cleanup_db(db_path: pathlib.Path) -> None:
    engine.dispose()
    gc.collect()
    for attempt in range(3):
        try:
            db_path.unlink(missing_ok=True)
            return
        except PermissionError:
            if attempt == 2:
                emit(f"WARNING | cleanup failed for {db_path.name}")
                return
            time.sleep(0.2)
            gc.collect()


if __name__ == "__main__":
    try:
        run()
        emit("")
        emit("=" * 50)
        emit(f"RESULTS: {passed} passed, {failed} failed")
        if failed:
            sys.exit(1)
    finally:
        _cleanup_db(DB_PATH)
