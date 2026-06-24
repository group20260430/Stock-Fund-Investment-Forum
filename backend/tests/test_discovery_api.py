"""Discovery & Search API tests. Covers spec section 2.6.

Endpoints: feed, hot, search, recommendations, search/recommendations, suggestions.

Run:  cd backend && python tests/test_discovery_api.py
"""

import gc
import os
import sys
import time
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite:///./test_discovery.db"
DB_PATH = Path("test_discovery.db")
DB_PATH.unlink(missing_ok=True)

import app.models  # noqa: F401
from app.db.base import Base
from app.db.session import SessionLocal, engine

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


def register(client, phone, nickname):
    r = client.post("/api/auth/register", json={
        "phone": phone, "password": "Discovery123", "nickname": nickname,
    })
    assert r.status_code == 201, r.text
    d = r.json()["data"]
    return d["user_id"], {"Authorization": f"Bearer {d['token']}"}


def run():
    with TestClient(app) as client:
        # ── Setup ───────────────────────────────────────────────────
        reader_id, reader_h = register(client, "13800005001", "Reader")
        author_id, author_h = register(client, "13800005002", "Analyst")
        cat_id = client.get("/api/categories").json()["data"][0]["id"]

        # Reader follows author → feed will show author's posts
        client.post(f"/api/users/{author_id}/follow", headers=reader_h)

        # Create post with tags for hot/search
        r = client.post("/api/posts", headers=author_h, json={
            "category_id": cat_id, "title": "沪深300定投分析",
            "content": "宽基指数长期定投策略", "tags": ["沪深300", "定投"],
        })
        assert r.status_code == 201, r.text

        # Create another post to have more content
        client.post("/api/posts", headers=author_h, json={
            "category_id": cat_id, "title": "A股市场分析",
            "content": "近期市场走势分析报告", "tags": ["A股"],
        })

        # Create a group for search
        client.post("/api/groups", headers=author_h, json={
            "name": "投资交流群", "description": "讨论股票投资策略",
        })

        # ══════════════════════════════════════════════════════════════
        # 1. Feed
        # ══════════════════════════════════════════════════════════════
        r = client.get("/api/feed", headers=reader_h)
        j = check("1.1 个性化Feed(已关注)", 200, r)
        assert r.status_code == 200, r.text
        assert j["data"]["total"] >= 1
        assert j["data"]["items"][0]["author"]["id"] == author_id

        r = client.get("/api/feed", headers=reader_h, params={"page": 1, "size": 1})
        j = check("1.2 Feed分页", 200, r)
        assert len(j["data"]["items"]) == 1

        # ══════════════════════════════════════════════════════════════
        # 2. Hot ranking
        # ══════════════════════════════════════════════════════════════
        r = client.get("/api/hot", params={"period": "daily"})
        j = check("2.1 日热榜", 200, r)
        assert isinstance(j["data"], list)

        r = client.get("/api/hot", params={"period": "weekly"})
        j = check("2.2 周热榜", 200, r)
        assert isinstance(j["data"], list)

        r = client.get("/api/hot", params={"period": "monthly"})
        j = check("2.3 月热榜", 200, r)
        assert isinstance(j["data"], list)

        # Empty hot (fresh DB — should return data or empty gracefully)
        r = client.get("/api/hot", params={"period": "daily"})
        check("2.4 热榜(有结果)", 200, r)

        # ══════════════════════════════════════════════════════════════
        # 3. Search
        # ══════════════════════════════════════════════════════════════
        r = client.get("/api/search", params={"keyword": "定投", "type": "post"})
        j = check("3.1 搜索帖子", 200, r)
        assert j["data"]["total"] >= 1

        r = client.get("/api/search", params={"keyword": "Analyst", "type": "user"})
        j = check("3.2 搜索用户", 200, r)
        if r.status_code == 200 and j["data"]["items"]:
            assert j["data"]["items"][0]["nickname"] == "Analyst"

        r = client.get("/api/search", params={"keyword": "000300", "type": "stock"})
        j = check("3.3 搜索股票", 200, r)
        if r.status_code == 200 and j["data"]["items"]:
            assert j["data"]["items"][0]["name"] == "沪深300"

        r = client.get("/api/search", params={"keyword": "投资", "type": "group"})
        j = check("3.4 搜索群组", 200, r)
        if r.status_code == 200:
            assert j["data"]["total"] >= 1

        r = client.get("/api/search", params={"keyword": "A股", "type": "all"})
        j = check("3.5 综合搜索(all)", 200, r)
        assert r.status_code == 200, r.text

        r = client.get("/api/search", params={"keyword": "不存在关键词XYZABC"})
        j = check("3.6 搜索无结果", 200, r)
        if r.status_code == 200:
            assert j["data"]["total"] == 0

        # ══════════════════════════════════════════════════════════════
        # 4. Recommendations
        # ══════════════════════════════════════════════════════════════
        r = client.get("/api/recommendations")
        j = check("4.1 匿名推荐(新用户/热门)", 200, r)
        assert r.status_code == 200, r.text
        assert "items" in j["data"]

        # Set investment tags for reader → personalized recommendations
        db = SessionLocal()
        from app.models.user import User
        u = db.query(User).filter(User.id == reader_id).first()
        u.investment_tags = ["A股", "定投"]
        db.commit()
        db.close()
        r = client.get("/api/recommendations", headers=reader_h)
        j = check("4.2 个性化推荐(有投资偏好)", 200, r)
        assert r.status_code == 200, r.text

        # ══════════════════════════════════════════════════════════════
        # 5. Search page recommendations
        # ══════════════════════════════════════════════════════════════
        r = client.get("/api/search/recommendations")
        j = check("5.1 搜索页推荐", 200, r)
        assert r.status_code == 200, r.text
        assert "posts" in j["data"]
        assert "users" in j["data"]
        assert "stocks" in j["data"]

        # ══════════════════════════════════════════════════════════════
        # 6. Search suggestions
        # ══════════════════════════════════════════════════════════════
        r = client.get("/api/search/suggestions", params={"keyword": "沪深"})
        j = check("6.1 搜索联想(股票匹配)", 200, r)
        if r.status_code == 200:
            assert len(j["data"]["stocks"]) >= 1

        r = client.get("/api/search/suggestions", params={"keyword": "000"})
        j = check("6.2 搜索联想(代码匹配)", 200, r)
        assert r.status_code == 200, r.text

        r = client.get("/api/search/suggestions", params={"keyword": ""})
        check("6.3 搜索联想(空输入→422)", 422, r)

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
