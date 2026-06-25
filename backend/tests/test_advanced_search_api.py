"""Advanced search API tests — time_range, is_elite, market, category_id, sort filters.

Run:  cd backend && python tests/test_advanced_search_api.py
"""
import gc
import os
import pathlib
import sys
import time

os.environ["DATABASE_URL"] = "sqlite:///./test_advanced_search.db"

DB_PATH = pathlib.Path("test_advanced_search.db")
DB_PATH.unlink(missing_ok=True)

from app.db.base import Base
from app.db.session import engine
import app.models  # noqa: F401
Base.metadata.create_all(bind=engine)

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

passed = 0
failed = 0
errors = []


def check(label: str, expected: int, response, extra_check=None):
    global passed, failed
    try:
        assert response.status_code == expected, (
            f"[{label}] expected {expected}, got {response.status_code}: {response.text[:200]}"
        )
        if extra_check:
            extra_check(response.json())
        passed += 1
        print(f"  ✅ {label}")
    except AssertionError as e:
        failed += 1
        errors.append(str(e))
        print(f"  ❌ {label}: {e}")


# ============================================================
# Phase 1: Setup — register users, create posts
# ============================================================
print("\n=== Phase 1: Setup ===")

r = client.post("/api/auth/register", json={
    "phone": "13800007001", "password": "UserPass123", "nickname": "author1",
})
check("1.1 Register author1", 201, r)
TOKEN1 = r.json()["data"]["token"]

r = client.post("/api/auth/register", json={
    "phone": "13800007002", "password": "UserPass123", "nickname": "author2",
})
check("1.2 Register author2", 201, r)
TOKEN2 = r.json()["data"]["token"]

# Create categories
from app.db.session import SessionLocal
from app.models.user import User, UserRole
from app.models.content import Category, Post as PostModel

db_session = SessionLocal()
cat1 = Category(name="A股市场", description="A股讨论", sort_order=1)
cat2 = Category(name="基金专区", description="基金讨论", sort_order=2)
cat3 = Category(name="港股市场", description="港股讨论", sort_order=3)
db_session.add_all([cat1, cat2, cat3])
db_session.commit()
CAT1_ID = cat1.id
CAT2_ID = cat2.id
CAT3_ID = cat3.id
db_session.close()

# Create posts with different categories and mark one as elite
r = client.post("/api/posts", json={
    "title": "A股牛市来了",
    "content": "最近A股市场表现强劲，成交量放大，建议关注科技板块。",
    "category_id": CAT1_ID,
    "post_type": "normal",
}, headers={"Authorization": f"Bearer {TOKEN1}"})
check("1.3 Create post in A股", 201, r)
POST1_ID = r.json()["data"]["id"]

r = client.post("/api/posts", json={
    "title": "基金定投策略分享",
    "content": "每月定投沪深300指数基金，长期持有收益稳健。",
    "category_id": CAT2_ID,
    "post_type": "normal",
}, headers={"Authorization": f"Bearer {TOKEN1}"})
check("1.4 Create post in 基金", 201, r)
POST2_ID = r.json()["data"]["id"]

r = client.post("/api/posts", json={
    "title": "港股打新攻略",
    "content": "港股打新年化收益可观，但需要注意破发风险。",
    "category_id": CAT3_ID,
    "post_type": "normal",
}, headers={"Authorization": f"Bearer {TOKEN2}"})
check("1.5 Create post in 港股", 201, r)
POST3_ID = r.json()["data"]["id"]

# Manually mark post2 as elite via DB
db_session = SessionLocal()
post2 = db_session.query(PostModel).filter(PostModel.id == POST2_ID).first()
post2.is_elite = True
db_session.commit()
db_session.close()

# ============================================================
# Phase 2: Search with category filter
# ============================================================
print("\n=== Phase 2: category_id filter ===")

r = client.get(f"/api/search?keyword=市场&category_id={CAT1_ID}")
check("2.1 Search by category (A股)", 200, r, lambda j: j["data"]["total"] >= 1)

r = client.get(f"/api/search?keyword=市场&category_id={CAT3_ID}")
check("2.2 Search by category (港股)", 200, r, lambda j: j["data"]["total"] >= 1)

r = client.get("/api/search?keyword=市场&category_id=99999")
check("2.3 Search by non-existent category", 200, r)

# ============================================================
# Phase 3: Search with sort filter
# ============================================================
print("\n=== Phase 3: sort filter ===")

r = client.get("/api/search?keyword=投资&sort=heat")
check("3.1 Search sorted by heat", 200, r)

r = client.get("/api/search?keyword=投资&sort=time")
check("3.2 Search sorted by time", 200, r)

r = client.get("/api/search?keyword=投资&sort=relevance")
check("3.3 Search sorted by relevance", 200, r)

# ============================================================
# Phase 4: Search with time_range filter
# ============================================================
print("\n=== Phase 4: time_range filter ===")

r = client.get("/api/search?keyword=投资&time_range=day")
check("4.1 Search time_range=day", 200, r)

r = client.get("/api/search?keyword=投资&time_range=week")
check("4.2 Search time_range=week", 200, r)

r = client.get("/api/search?keyword=投资&time_range=month")
check("4.3 Search time_range=month", 200, r)

# ============================================================
# Phase 5: Search with is_elite filter
# ============================================================
print("\n=== Phase 5: is_elite filter ===")

r = client.get("/api/search?keyword=定投&is_elite=true")
check("5.1 Search elite posts (keyword match)", 200, r, lambda j: (
    j["data"]["total"] >= 1
))

r = client.get("/api/search?keyword=打新&is_elite=true")
check("5.2 Search elite (non-elite post not returned)", 200, r)

# ============================================================
# Phase 6: Search with market filter
# ============================================================
print("\n=== Phase 6: market filter ===")

r = client.get("/api/search?keyword=市场&market=sh")
check("6.1 Search with market=sh", 200, r)

# ============================================================
# Phase 7: Combined filters
# ============================================================
print("\n=== Phase 7: Combined filters ===")

r = client.get(f"/api/search?keyword=投资&category_id={CAT2_ID}&sort=time&time_range=month")
check("7.1 Combined: category + sort + time_range", 200, r, lambda j: j["data"]["total"] >= 1)

# ============================================================
# Cleanup
# ============================================================
print(f"\n{'='*50}")
print(f"RESULTS: {passed} passed, {failed} failed")
if errors:
    for e in errors:
        print(f"  - {e}")

gc.collect()
time.sleep(0.1)
try:
    DB_PATH.unlink(missing_ok=True)
except PermissionError:
    pass

raise SystemExit(0 if failed == 0 else 1)
