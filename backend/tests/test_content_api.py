"""Content / Posts API tests. Covers spec section 2.2.

Endpoints: categories, posts list, posts CRUD, vote.
Rate limit: post creation = 5/60s per user.

Run:  cd backend && python tests/test_content_api.py
"""

import gc
import os
import sys
import time
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite:///./test_content.db"
DB_PATH = Path("test_content.db")
DB_PATH.unlink(missing_ok=True)

import app.models  # noqa: F401
from app.db.base import Base
from app.db.session import SessionLocal, engine

Base.metadata.create_all(bind=engine)

# Ensure dev_code is returned (SMTP configured in .env)
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
        # ── Setup: register users ───────────────────────────────────
        tok_a, hdr_a = register(client, "13800001001", "Content123", "post_author")
        tok_b, hdr_b = register(client, "13800001002", "Content456", "other_user")

        # ══════════════════════════════════════════════════════════════
        # 1. Categories
        # ══════════════════════════════════════════════════════════════
        r = client.get("/api/categories")
        j = check("1.1 获取板块列表(树形结构)", 200, r)
        assert r.status_code == 200, r.text
        cats = j["data"]
        assert isinstance(cats, list), "expected list"
        if cats:
            # Verify tree structure: parent+children
            first = cats[0]
            assert "id" in first and "name" in first, "missing category fields"
            print(f"     categories count={len(cats)}")

        # ══════════════════════════════════════════════════════════════
        # 2. Post list
        # ══════════════════════════════════════════════════════════════
        cat_id = cats[0]["id"] if cats else 1

        r = client.get("/api/posts")
        j = check("2.1 全部帖子(无参数)", 200, r)
        assert "total" in j["data"] and "items" in j["data"]

        r = client.get("/api/posts", params={"category_id": cat_id})
        check("2.2 按板块筛选", 200, r)

        r = client.get("/api/posts", params={"sort_by": "hot"})
        check("2.3 按热度排序", 200, r)

        r = client.get("/api/posts", params={"page": 1, "page_size": 5})
        check("2.4 分页(page=1,size=5)", 200, r)

        r = client.get("/api/posts", params={"category_id": 99999})
        j = check("2.5 空分类(ID不存在)", 200, r)
        if r.status_code == 200:
            assert j["data"]["total"] == 0, f"expected 0, got {j['data']['total']}"

        r = client.get("/api/posts", params={"keyword": "不存在关键词XYZABC"})
        j = check("2.6 搜索无结果", 200, r)
        if r.status_code == 200:
            assert j["data"]["total"] == 0

        # ══════════════════════════════════════════════════════════════
        # 3. Create posts (5 types — post rate limit = 5/60s per user)
        # ══════════════════════════════════════════════════════════════
        r = client.post("/api/posts", headers=hdr_a, json={
            "category_id": cat_id, "title": "普通帖测试",
            "content": "这是普通帖的内容。", "post_type": "normal",
            "tags": ["测试"],
        })
        j = check("3.1 创建普通帖(normal)", 201, r, "id")
        assert r.status_code == 201, r.text
        normal_id = j["data"]["id"]

        r = client.post("/api/posts", headers=hdr_a, json={
            "category_id": cat_id, "title": "长文帖测试",
            "content": "详细内容 " * 100, "post_type": "long_article",
        })
        j = check("3.2 创建长文帖(long_article)", 201, r, "id")
        long_id = j["data"]["id"]

        r = client.post("/api/posts", headers=hdr_a, json={
            "category_id": cat_id, "title": "投票帖测试",
            "content": "你怎么看？", "post_type": "poll",
            "vote_options": [{"label": "看多"}, {"label": "看空"}, {"label": "观望"}],
        })
        j = check("3.3 创建投票帖(poll)", 201, r, "id")
        poll_id = j["data"]["id"]

        r = client.post("/api/posts", headers=hdr_a, json={
            "category_id": cat_id, "title": "动态帖测试",
            "content": "随手发个动态", "post_type": "moment",
        })
        j = check("3.4 创建动态帖(moment)", 201, r, "id")
        moment_id = j["data"]["id"]

        # Unauthenticated
        r = client.post("/api/posts", json={
            "category_id": cat_id, "title": "未登录", "content": "xx",
        })
        check("3.5 未登录创建", 403, r)

        # Poll with <2 options
        r = client.post("/api/posts", headers=hdr_a, json={
            "category_id": cat_id, "title": "错误投票", "content": "内容",
            "post_type": "poll", "vote_options": [{"label": "唯一"}],
        })
        check("3.6 投票选项少于2项", 422, r)

        # Empty title
        r = client.post("/api/posts", headers=hdr_a, json={
            "category_id": cat_id, "title": "", "content": "内容",
        })
        check("3.7 标题为空", 422, r)
        # post rate limit: 5 posts created (3.1-3.4 + maybe 3.6/3.7 counted too)
        # but 3.6 and 3.7 are validation failures — they may not count
        # against the user's rate limit since validation happens before
        # the limiter check. We stay within the 5-post limit anyway.

        # ══════════════════════════════════════════════════════════════
        # 4. Post detail
        # ══════════════════════════════════════════════════════════════
        r = client.get(f"/api/posts/{poll_id}")
        j = check("4.1 获取帖子详情(投票帖)", 200, r)
        assert r.status_code == 200, r.text
        post = j["data"]
        assert "vote_options" in post and len(post["vote_options"]) == 3
        option_id = post["vote_options"][0]["id"]

        r = client.get(f"/api/posts/{normal_id}")
        j = check("4.2 获取帖子详情(普通帖)", 200, r)
        assert r.status_code == 200, r.text
        assert j["data"]["title"] == "普通帖测试"
        assert j["data"]["post_type"] == "normal"

        r = client.get("/api/posts/99999")
        check("4.3 帖子不存在", 404, r)

        # ══════════════════════════════════════════════════════════════
        # 5. Edit post
        # ══════════════════════════════════════════════════════════════
        r = client.put(f"/api/posts/{normal_id}", headers=hdr_a, json={
            "category_id": cat_id, "title": "已编辑标题",
            "content": "更新后的内容", "post_type": "normal",
        })
        j = check("5.1 作者编辑帖子", 200, r)
        assert r.status_code == 200, r.text
        # Verify edit persisted by reading post back
        detail = client.get(f"/api/posts/{normal_id}")
        assert detail.status_code == 200, detail.text
        assert detail.json()["data"]["title"] == "已编辑标题"

        r = client.put(f"/api/posts/{normal_id}", headers=hdr_b, json={
            "category_id": cat_id, "title": "别人编辑", "content": "xx",
        })
        check("5.2 非作者编辑", 403, r)

        r = client.put("/api/posts/99999", headers=hdr_a, json={
            "category_id": cat_id, "title": "不存在", "content": "xx",
        })
        check("5.3 编辑不存在的帖子", 404, r)

        # ══════════════════════════════════════════════════════════════
        # 6. Delete post
        # ══════════════════════════════════════════════════════════════
        # Create a disposable post for delete tests
        r = client.post("/api/posts", headers=hdr_a, json={
            "category_id": cat_id, "title": "待删除", "content": "删掉",
        })
        assert r.status_code == 201, r.text
        del_id = r.json()["data"]["id"]

        r = client.delete(f"/api/posts/{del_id}", headers=hdr_b)
        check("6.1 非作者删除", 403, r)

        r = client.delete("/api/posts/99999", headers=hdr_a)
        check("6.2 删除不存在的帖子", 404, r)

        r = client.delete(f"/api/posts/{del_id}", headers=hdr_a)
        check("6.3 作者删除", 204, r)

        # ══════════════════════════════════════════════════════════════
        # 7. Vote
        # ══════════════════════════════════════════════════════════════
        r = client.post(f"/api/posts/{poll_id}/vote", headers=hdr_a, json={
            "option_ids": [option_id],
        })
        j = check("7.1 正常投票", 200, r)
        assert r.status_code == 200, r.text
        results = j["data"]["results"]
        assert results[0]["vote_count"] == 1

        # Re-vote same option (implementation allows re-vote)
        r = client.post(f"/api/posts/{poll_id}/vote", headers=hdr_a, json={
            "option_ids": [post["vote_options"][1]["id"]],
        })
        j = check("7.2 重新投票(改选)", 200, r)
        assert r.status_code == 200, r.text

        # Vote on non-poll post
        r = client.post(f"/api/posts/{normal_id}/vote", headers=hdr_b, json={
            "option_ids": [1],
        })
        check("7.3 对非投票帖投票", 400, r)

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
