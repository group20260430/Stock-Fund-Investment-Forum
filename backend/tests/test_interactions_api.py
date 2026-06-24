"""Interactions API tests. Covers spec section 2.3.

Comments, likes, collections, shares — adds edge cases to existing coverage.

Run:  cd backend && python tests/test_interactions_api.py
"""

import gc
import os
import sys
import time
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite:///./test_interactions.db"
DB_PATH = Path("test_interactions.db")
DB_PATH.unlink(missing_ok=True)

import app.models  # noqa: F401
from app.db.base import Base
from app.db.session import engine

Base.metadata.create_all(bind=engine)

from unittest.mock import PropertyMock, patch
from app.core.config import Settings
_patch_smtp = patch.object(Settings, "smtp_configured", new_callable=PropertyMock)
_patch_smtp.start().return_value = False

from fastapi.testclient import TestClient
from app.main import app

passed = 0
failed = 0


def check(label, expect, response, show_key=None):
    global passed, failed
    try:
        j = response.json()
    except Exception:
        j = {"detail": "(non-JSON body)"}
    ok = response.status_code == expect
    if ok:
        passed += 1
        marker = "OK"
    else:
        failed += 1
        marker = "FAIL"
    msg = j.get("message", j.get("detail", ""))
    print(f"{marker} | {label}: HTTP {response.status_code} | {msg}")
    if not ok:
        print(f"     EXPECTED {expect}, GOT {response.status_code}")
        print(f"     Full response: {j}")
    if show_key and ok and "data" in j:
        d = j["data"]
        if isinstance(d, dict) and show_key in d:
            print(f"     {show_key}={d[show_key]}")
    return j


def register(client, phone, password, nickname):
    r = client.post("/api/auth/register", json={
        "phone": phone, "password": password, "nickname": nickname,
    })
    assert r.status_code == 201, r.text
    d = r.json()["data"]
    return d["token"], {"Authorization": f"Bearer {d['token']}"}


def run():
    with TestClient(app) as client:
        # ── Setup ───────────────────────────────────────────────────
        tok_a, hdr_a = register(client, "13800002001", "Interact123", "interactor")
        tok_b, hdr_b = register(client, "13800002002", "Interact456", "other_user")
        cat_id = client.get("/api/categories").json()["data"][0]["id"]

        # Create a post for testing
        r = client.post("/api/posts", headers=hdr_a, json={
            "category_id": cat_id, "title": "互动测试帖", "content": "测试评论、点赞、收藏和分享",
        })
        assert r.status_code == 201, r.text
        post_id = r.json()["data"]["id"]

        # ══════════════════════════════════════════════════════════════
        # 1. Comments — list
        # ══════════════════════════════════════════════════════════════
        r = client.get(f"/api/posts/{post_id}/comments")
        j = check("1.1 评论列表(无评论)", 200, r)
        assert r.status_code == 200, r.text
        assert j["data"]["total"] == 0

        r = client.get("/api/posts/99999/comments")
        check("1.2 评论列表(帖子不存在)", 404, r)

        # ══════════════════════════════════════════════════════════════
        # 2. Comments — create
        # ══════════════════════════════════════════════════════════════
        r = client.post(f"/api/posts/{post_id}/comments", headers=hdr_a, json={
            "content": "一级评论：好文章！",
        })
        j = check("2.1 发表一级评论", 201, r, "id")
        root_id = j["data"]["id"]

        r = client.post(f"/api/posts/{post_id}/comments", headers=hdr_a, json={
            "content": "回复：同意", "parent_id": root_id, "reply_to_id": root_id,
        })
        j = check("2.2 发表楼中楼回复", 201, r, "id")
        assert j["data"]["id"] is not None

        r = client.post(f"/api/posts/{post_id}/comments", json={
            "content": "未登录评论",
        })
        check("2.3 未登录发表评论", 403, r)

        r = client.post(f"/api/posts/{post_id}/comments", headers=hdr_a, json={
            "content": "",
        })
        check("2.4 空内容评论", 422, r)

        # ══════════════════════════════════════════════════════════════
        # 3. Comments — like
        # ══════════════════════════════════════════════════════════════
        r = client.post(f"/api/comments/{root_id}/like", headers=hdr_a)
        j = check("3.1 评论点赞", 200, r)
        assert j["data"]["is_liked"] is True
        assert j["data"]["like_count"] == 1

        r = client.post(f"/api/comments/{root_id}/like", headers=hdr_a)
        j = check("3.2 取消评论点赞", 200, r)
        assert j["data"]["is_liked"] is False
        assert j["data"]["like_count"] == 0

        # ══════════════════════════════════════════════════════════════
        # 4. Comments — delete
        # ══════════════════════════════════════════════════════════════
        # Create a comment to delete
        r = client.post(f"/api/posts/{post_id}/comments", headers=hdr_a, json={
            "content": "这条评论将被删除",
        })
        assert r.status_code == 201, r.text
        del_comment_id = r.json()["data"]["id"]

        r = client.delete(f"/api/comments/{del_comment_id}", headers=hdr_b)
        check("4.1 非作者删除评论", 403, r)

        r = client.delete("/api/comments/99999", headers=hdr_a)
        check("4.2 删除不存在的评论", 404, r)

        r = client.delete(f"/api/comments/{del_comment_id}", headers=hdr_a)
        check("4.3 作者删除评论", 204, r)

        # ══════════════════════════════════════════════════════════════
        # 5. Post like — verify like_count
        # ══════════════════════════════════════════════════════════════
        detail_before = client.get(f"/api/posts/{post_id}").json()["data"]
        lc_before = detail_before["like_count"]

        r = client.post(f"/api/posts/{post_id}/like", headers=hdr_a)
        j = check("5.1 帖子点赞", 200, r)
        assert j["data"]["is_liked"] is True
        assert j["data"]["like_count"] == lc_before + 1

        r = client.post(f"/api/posts/{post_id}/like", headers=hdr_a)
        j = check("5.2 取消帖子点赞", 200, r)
        assert j["data"]["is_liked"] is False
        assert j["data"]["like_count"] == lc_before

        # ══════════════════════════════════════════════════════════════
        # 6. Collect / Collections
        # ══════════════════════════════════════════════════════════════
        r = client.post(f"/api/posts/{post_id}/collect", headers=hdr_a, json={
            "folder_name": "研究",
        })
        j = check("6.1 收藏帖子", 200, r)
        assert j["data"]["is_collected"] is True

        r = client.get("/api/users/me/collections", headers=hdr_a)
        j = check("6.2 获取收藏列表(有收藏)", 200, r)
        assert j["data"]["total"] >= 1
        assert j["data"]["items"][0]["folder_name"] == "研究"

        r = client.post(f"/api/posts/{post_id}/collect", headers=hdr_a, json={
            "folder_name": "研究",
        })
        j = check("6.3 取消收藏", 200, r)
        assert j["data"]["is_collected"] is False

        r = client.get("/api/users/me/collections", headers=hdr_b)
        j = check("6.4 获取收藏列表(无收藏)", 200, r)
        assert r.status_code == 200, r.text
        assert j["data"]["total"] == 0

        # ══════════════════════════════════════════════════════════════
        # 7. Share
        # ══════════════════════════════════════════════════════════════
        r = client.post(f"/api/posts/{post_id}/share", headers=hdr_a, json={
            "share_type": "timeline", "comment": "值得一看",
        })
        j = check("7.1 转发到动态(timeline)", 201, r)
        assert j["data"]["share_count"] >= 1

        r = client.post(f"/api/posts/{post_id}/share", headers=hdr_a, json={
            "share_type": "message",
        })
        check("7.2 转发到私信(message)", 201, r)

        r = client.post(f"/api/posts/{post_id}/share", json={
            "share_type": "timeline",
        })
        check("7.3 未登录转发", 403, r)

        # ══════════════════════════════════════════════════════════════
        # 8. Nested comment list verification
        # ══════════════════════════════════════════════════════════════
        r = client.get(f"/api/posts/{post_id}/comments", headers=hdr_a)
        j = check("8.1 评论列表(含嵌套回复)", 200, r)
        assert r.status_code == 200, r.text
        assert j["data"]["total"] >= 1
        root_comments = j["data"]["items"]
        if root_comments:
            found_replies = any(len(c.get("replies", [])) > 0 for c in root_comments)
            print(f"     has_replies={found_replies}")

    # ── Cleanup ────────────────────────────────────────────────────
    engine.dispose()
    gc.collect()
    for attempt in range(3):
        try:
            DB_PATH.unlink(missing_ok=True)
            break
        except PermissionError:
            if attempt == 2:
                print("WARNING | cleanup failed")
            time.sleep(0.2)
            gc.collect()


if __name__ == "__main__":
    exit_code = 0
    try:
        run()
    except Exception:
        import traceback
        traceback.print_exc()
        exit_code = 1
    finally:
        _patch_smtp.stop()
    print(f"\n{'='*60}")
    print(f"RESULTS: {passed} passed, {failed} failed")
    print(f"{'='*60}")
    sys.exit(exit_code)
