"""Admin category CRUD API tests — update, delete, reorder categories.

Run:  cd backend && python tests/test_admin_category_api.py
"""
import gc
import os
import pathlib
import sys
import time

os.environ["DATABASE_URL"] = "sqlite:///./test_admin_category.db"

DB_PATH = pathlib.Path("test_admin_category.db")
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
# Phase 1: Setup admin + normal user
# ============================================================
print("\n=== Phase 1: Setup ===")

r = client.post("/api/auth/register", json={
    "phone": "13800003001",
    "password": "AdminPass123",
    "nickname": "cat_admin",
})
check("1.1 Register admin", 201, r)
ADMIN_TOKEN = r.json()["data"]["token"]

# Promote to admin
from app.db.session import SessionLocal
from app.models.user import User, UserRole

db_session = SessionLocal()
db_session.query(User).filter(User.phone == "13800003001").update({"role": UserRole.ADMIN})
db_session.commit()
db_session.close()

r = client.post("/api/auth/register", json={
    "phone": "13800003002",
    "password": "UserPass123",
    "nickname": "cat_user",
})
check("1.2 Register normal user", 201, r)
USER_TOKEN = r.json()["data"]["token"]

# ============================================================
# Phase 2: Create categories
# ============================================================
print("\n=== Phase 2: Create categories ===")

r = client.post("/api/admin/categories", json={
    "name": "股票讨论区",
    "description": "股票相关讨论",
    "sort_order": 1,
}, headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
check("2.1 Create top-level category", 201, r, lambda j: "id" in j["data"])
CAT1_ID = r.json()["data"]["id"]

r = client.post("/api/admin/categories", json={
    "name": "基金专区",
    "description": "基金投资讨论",
    "sort_order": 2,
}, headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
check("2.2 Create second category", 201, r)
CAT2_ID = r.json()["data"]["id"]

r = client.post("/api/admin/categories", json={
    "name": "A股讨论",
    "description": "A股市场讨论",
    "parent_id": CAT1_ID,
    "sort_order": 1,
}, headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
check("2.3 Create sub-category under 股票讨论区", 201, r)
SUBCAT_ID = r.json()["data"]["id"]

# Non-admin cannot create
r = client.post("/api/admin/categories", json={
    "name": "黑客创建",
    "description": "should fail",
}, headers={"Authorization": f"Bearer {USER_TOKEN}"})
check("2.4 Non-admin create → 403", 403, r)

# ============================================================
# Phase 3: Update categories
# ============================================================
print("\n=== Phase 3: Update categories ===")

r = client.put(f"/api/admin/categories/{CAT1_ID}", json={
    "name": "股票讨论区(更新)",
    "description": "更新后的描述",
    "sort_order": 10,
}, headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
check("3.1 Update category name & description", 200, r)

# Verify update by listing
r = client.get("/api/categories")
check("3.2 Verify updated name in list", 200, r, lambda j: (
    any(c["name"] == "股票讨论区(更新)" for c in j["data"])
))

# Non-admin cannot update
r = client.put(f"/api/admin/categories/{CAT2_ID}", json={
    "name": "篡改名称",
}, headers={"Authorization": f"Bearer {USER_TOKEN}"})
check("3.3 Non-admin update → 403", 403, r)

# ============================================================
# Phase 4: Reorder categories
# ============================================================
print("\n=== Phase 4: Reorder categories ===")

r = client.post("/api/admin/categories/reorder", json={
    "order": [CAT2_ID, CAT1_ID],
}, headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
check("4.1 Reorder categories", 200, r)

# ============================================================
# Phase 5: Delete category
# ============================================================
print("\n=== Phase 5: Delete categories ===")

# Delete sub-category first
r = client.delete(f"/api/admin/categories/{SUBCAT_ID}",
                  headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
check("5.1 Delete sub-category", 204, r)

# Delete top-level category
r = client.delete(f"/api/admin/categories/{CAT1_ID}",
                  headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
check("5.2 Delete top-level category", 204, r)

# Verify deletion
r = client.get("/api/categories")
check("5.3 Verify deleted categories gone", 200, r, lambda j: (
    all(c["id"] != CAT1_ID for c in j["data"])
))

# Delete non-existent
r = client.delete("/api/admin/categories/99999",
                  headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
check("5.4 Delete non-existent → 404", 404, r)

# Non-admin cannot delete
r = client.delete(f"/api/admin/categories/{CAT2_ID}",
                  headers={"Authorization": f"Bearer {USER_TOKEN}"})
check("5.5 Non-admin delete → 403", 403, r)

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
