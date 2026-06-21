import os
import pathlib
import sys

os.environ["DATABASE_URL"] = "sqlite:///./test_sensitive_filter.db"

DB_PATH = pathlib.Path("test_sensitive_filter.db")
DB_PATH.unlink(missing_ok=True)

import app.models  # noqa: F401
from fastapi.testclient import TestClient

from app.db.session import SessionLocal, engine
from app.main import app
from app.models.content import Comment, CommentStatus, Post, PostStatus
from app.models.operations import SensitiveLevel, SensitiveWord

passed = 0
failed = 0


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
    print(f"{marker} | {label}: HTTP {response.status_code} | {message}")
    if not ok:
        print(f"     EXPECTED {expect}, GOT {response.status_code}")
        print(f"     Full response: {body}")
    return ok, body


def insert_sensitive_words() -> None:
    db = SessionLocal()
    try:
        db.add_all(
            [
                SensitiveWord(word="禁发词", level=SensitiveLevel.BLOCK, is_active=True),
                SensitiveWord(word="审核词", level=SensitiveLevel.REVIEW, is_active=True),
                SensitiveWord(word="提醒词", level=SensitiveLevel.WARN, is_active=True),
                SensitiveWord(word="停用词", level=SensitiveLevel.BLOCK, is_active=False),
            ]
        )
        db.commit()
    finally:
        db.close()


def fetch_post_status(post_id: int) -> str | None:
    db = SessionLocal()
    try:
        post = db.query(Post).filter(Post.id == post_id).first()
        return post.status.value if post else None
    finally:
        db.close()


def fetch_comment_status(comment_id: int) -> str | None:
    db = SessionLocal()
    try:
        comment = db.query(Comment).filter(Comment.id == comment_id).first()
        return comment.status.value if comment else None
    finally:
        db.close()


def create_safe_post(client: TestClient, headers: dict[str, str], category_id: int, suffix: str) -> int:
    response = client.post(
        "/api/posts",
        headers=headers,
        json={
            "category_id": category_id,
            "title": f"安全帖子{suffix}",
            "content": f"这是一条用于评论测试的安全内容 {suffix}",
            "post_type": "normal",
            "status": "published",
            "tags": [],
            "attachments": [],
            "vote_options": [],
        },
    )
    ok, body = check(f"setup post {suffix}", 201, response)
    if not ok:
        raise RuntimeError("failed to create setup post")
    return body["data"]["id"]


def run() -> None:
    with TestClient(app) as client:
        register = client.post(
            "/api/auth/register",
            json={"phone": "13800009991", "password": "Sensitive123", "nickname": "filter_user"},
        )
        ok, body = check("register", 201, register)
        if not ok:
            return
        token = body["data"]["token"]
        headers = {"Authorization": f"Bearer {token}"}

        categories = client.get("/api/categories")
        ok, body = check("categories", 200, categories)
        if not ok:
            return
        category_id = body["data"][0]["id"]

        insert_sensitive_words()

        blocked_post = client.post(
            "/api/posts",
            headers=headers,
            json={
                "category_id": category_id,
                "title": "标题包含禁发词",
                "content": "正常内容",
                "post_type": "normal",
                "status": "published",
                "tags": [],
                "attachments": [],
                "vote_options": [],
            },
        )
        check("post block title", 400, blocked_post)

        review_post = client.post(
            "/api/posts",
            headers=headers,
            json={
                "category_id": category_id,
                "title": "审核帖子",
                "content": "这里包含审核词，需要进入审核",
                "post_type": "normal",
                "status": "published",
                "tags": [],
                "attachments": [],
                "vote_options": [],
            },
        )
        ok, body = check("post review content", 201, review_post)
        if ok:
            status = fetch_post_status(body["data"]["id"])
            if status == PostStatus.REVIEWING.value:
                print("OK | post review status: REVIEWING")
                global passed
                passed += 1
            else:
                print(f"FAIL | post review status: expected REVIEWING, got {status}")
                global failed
                failed += 1

        warn_post = client.post(
            "/api/posts",
            headers=headers,
            json={
                "category_id": category_id,
                "title": "提醒帖子",
                "content": "这里包含提醒词，但应正常发布",
                "post_type": "normal",
                "status": "published",
                "tags": [],
                "attachments": [],
                "vote_options": [],
            },
        )
        ok, body = check("post warn content", 201, warn_post)
        if ok:
            status = fetch_post_status(body["data"]["id"])
            if status == PostStatus.PUBLISHED.value:
                print("OK | post warn status: PUBLISHED")
                passed += 1
            else:
                print(f"FAIL | post warn status: expected PUBLISHED, got {status}")
                failed += 1

        inactive_post = client.post(
            "/api/posts",
            headers=headers,
            json={
                "category_id": category_id,
                "title": "停用词帖子",
                "content": "这里包含停用词，但不应被拦截",
                "post_type": "normal",
                "status": "published",
                "tags": [],
                "attachments": [],
                "vote_options": [],
            },
        )
        ok, body = check("post inactive word", 201, inactive_post)
        if ok:
            status = fetch_post_status(body["data"]["id"])
            if status == PostStatus.PUBLISHED.value:
                print("OK | post inactive status: PUBLISHED")
                passed += 1
            else:
                print(f"FAIL | post inactive status: expected PUBLISHED, got {status}")
                failed += 1

        post_for_block_comment = create_safe_post(client, headers, category_id, "A")
        blocked_comment = client.post(
            f"/api/posts/{post_for_block_comment}/comments",
            headers=headers,
            json={"content": "评论里有禁发词"},
        )
        check("comment block content", 400, blocked_comment)

        post_for_review_comment = create_safe_post(client, headers, category_id, "B")
        review_comment = client.post(
            f"/api/posts/{post_for_review_comment}/comments",
            headers=headers,
            json={"content": "评论里有审核词，需要审核"},
        )
        ok, body = check("comment review content", 201, review_comment)
        if ok:
            status = fetch_comment_status(body["data"]["id"])
            if status == CommentStatus.REVIEWING.value:
                print("OK | comment review status: REVIEWING")
                passed += 1
            else:
                print(f"FAIL | comment review status: expected REVIEWING, got {status}")
                failed += 1

        post_for_warn_comment = create_safe_post(client, headers, category_id, "C")
        warn_comment = client.post(
            f"/api/posts/{post_for_warn_comment}/comments",
            headers=headers,
            json={"content": "评论里有提醒词，但可发布"},
        )
        ok, body = check("comment warn content", 201, warn_comment)
        if ok:
            status = fetch_comment_status(body["data"]["id"])
            if status == CommentStatus.PUBLISHED.value:
                print("OK | comment warn status: PUBLISHED")
                passed += 1
            else:
                print(f"FAIL | comment warn status: expected PUBLISHED, got {status}")
                failed += 1


if __name__ == "__main__":
    try:
        run()
        print()
        print("=" * 50)
        print(f"RESULTS: {passed} passed, {failed} failed")
        if failed:
            sys.exit(1)
    finally:
        engine.dispose()
        DB_PATH.unlink(missing_ok=True)
