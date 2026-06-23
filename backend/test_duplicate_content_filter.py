import gc
import os
import pathlib
import sys
import time

os.environ["DATABASE_URL"] = "sqlite:///./test_duplicate_content_filter.db"

DB_PATH = pathlib.Path("test_duplicate_content_filter.db")
DB_PATH.unlink(missing_ok=True)

import app.models  # noqa: F401
from fastapi.testclient import TestClient

from app.db.session import SessionLocal, engine
from app.main import app
from app.models.content import Post, PostStatus
from app.models.operations import SensitiveLevel, SensitiveWord

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
        json={"phone": phone, "password": "Duplicate123", "nickname": nickname},
    )
    ok, body = check(f"register {nickname}", 201, response)
    if not ok:
        raise RuntimeError(f"failed to register {nickname}")
    token = body["data"]["token"]
    return {
        "headers": {"Authorization": f"Bearer {token}"},
        "user_id": body["data"]["user_id"],
    }


def insert_sensitive_words() -> None:
    db = SessionLocal()
    try:
        db.add(SensitiveWord(word="禁发词", level=SensitiveLevel.BLOCK, is_active=True))
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


def create_post(
    client: TestClient,
    headers: dict[str, str],
    category_id: int,
    title: str,
    content: str,
):
    return client.post(
        "/api/posts",
        headers=headers,
        json={
            "category_id": category_id,
            "title": title,
            "content": content,
            "post_type": "normal",
            "status": "published",
            "tags": [],
            "attachments": [],
            "vote_options": [],
        },
    )


def expect_post_status(label: str, post_id: int, expected: PostStatus) -> None:
    global passed, failed
    status = fetch_post_status(post_id)
    if status == expected.value:
        passed += 1
        emit(f"OK | {label}: {expected.name}")
    else:
        failed += 1
        emit(f"FAIL | {label}: expected {expected.name}, got {status}")


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


def run() -> None:
    with TestClient(app) as client:
        user_a = register_user(client, "13800009981", "dup_a")
        user_b = register_user(client, "13800009982", "dup_b")

        categories = client.get("/api/categories")
        ok, body = check("categories", 200, categories)
        if not ok:
            return
        category_id = body["data"][0]["id"]

        insert_sensitive_words()

        normal_post = create_post(
            client,
            user_a["headers"],
            category_id,
            "价值投资复盘一",
            "这是一次关于长期价值投资、估值、仓位管理和风险分散的详细复盘内容。",
        )
        ok, body = check("first post", 201, normal_post)
        if ok:
            expect_post_status("first post status", body["data"]["id"], PostStatus.PUBLISHED)

        exact_duplicate = create_post(
            client,
            user_a["headers"],
            category_id,
            "价值投资复盘一",
            "这是一次关于长期价值投资、估值、仓位管理和风险分散的详细复盘内容。",
        )
        check("exact duplicate", 400, exact_duplicate)

        near_duplicate = create_post(
            client,
            user_a["headers"],
            category_id,
            "价值投资复盘二",
            "这是一次关于长期价值投资、估值、仓位管理以及风险分散的详细复盘内容。",
        )
        ok, body = check("near duplicate", 201, near_duplicate)
        if ok:
            expect_post_status("near duplicate status", body["data"]["id"], PostStatus.REVIEWING)

        cross_user_duplicate = create_post(
            client,
            user_b["headers"],
            category_id,
            "价值投资复盘一",
            "这是一次关于长期价值投资、估值、仓位管理和风险分散的详细复盘内容。",
        )
        ok, body = check("cross user duplicate", 201, cross_user_duplicate)
        if ok:
            expect_post_status("cross user duplicate status", body["data"]["id"], PostStatus.PUBLISHED)

        short_post_a = create_post(
            client,
            user_a["headers"],
            category_id,
            "短帖",
            "你好世界",
        )
        ok, body = check("short post first", 201, short_post_a)
        if ok:
            expect_post_status("short post first status", body["data"]["id"], PostStatus.PUBLISHED)

        short_post_b = create_post(
            client,
            user_a["headers"],
            category_id,
            "短帖",
            "你好世界",
        )
        ok, body = check("short post duplicate skipped", 201, short_post_b)
        if ok:
            expect_post_status("short post duplicate skipped status", body["data"]["id"], PostStatus.PUBLISHED)

        sensitive_priority = create_post(
            client,
            user_a["headers"],
            category_id,
            "禁发词重复测试",
            "这是一次关于长期价值投资、估值、仓位管理和风险分散的详细复盘内容。",
        )
        check("sensitive block priority", 400, sensitive_priority)

        normal_followup = create_post(
            client,
            user_a["headers"],
            category_id,
            "宏观观察记录",
            "今天只记录市场流动性、行业轮动和仓位纪律，不涉及重复内容。",
        )
        ok, body = check("normal publish unaffected", 201, normal_followup)
        if ok:
            expect_post_status("normal publish unaffected status", body["data"]["id"], PostStatus.PUBLISHED)


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
