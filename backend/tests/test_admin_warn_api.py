"""Admin warn API tests — warning flow, notification, warn_count tracking.

Run:  cd backend && python tests/test_admin_warn_api.py
"""
import gc
import os
import pathlib
import sys
import time

os.environ["DATABASE_URL"] = "sqlite:///./test_admin_warn.db"

DB_PATH = pathlib.Path("test_admin_warn.db")
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
# Phase 1: Setup
# ============================================================
print("\n=== Phase 1: Setup ===")

r = client.post("/api/auth/register", json={
    "phone": "13800004001",
    "password": "AdminPass123",
    "nickname": "warn_admin",
})
check("1.1 Register admin", 201, r)
ADMIN_TOKEN = r.json()["data"]["token"]

from app.db.session import SessionLocal
from app.models.user import User, UserRole

db_session = SessionLocal()
admin_user = db_session.query(User).filter(User.phone == "13800004001").first()
admin_user.role = UserRole.ADMIN
ADMIN_USER_ID = admin_user.id
db_session.commit()
db_session.close()

r = client.post("/api/auth/register", json={
    "phone": "13800004002",
    "password": "UserPass123",
    "nickname": "warn_target",
})
check("1.2 Register target user", 201, r)
TARGET_TOKEN = r.json()["data"]["token"]
TARGET_ID = r.json()["data"]["user"]["id"]

r = client.post("/api/auth/register", json={
    "phone": "13800004003",
    "password": "UserPass123",
    "nickname": "normal_user",
})
check("1.3 Register normal user (non-admin)", 201, r)
USER_TOKEN = r.json()["data"]["token"]

db_session.close()

# ============================================================
# Phase 2: Admin warns user
# ============================================================
print("\n=== Phase 2: Admin warn ===")

r = client.post(f"/api/admin/users/{TARGET_ID}/ban", json={
    "action": "warn",
    "reason": "违规荐股",
}, headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
check("2.1 Admin warn user", 200, r, lambda j: (
    j["data"]["action"] == "warn"
    and j["data"]["warn_count"] == 1
))

# User should still be active (not banned)
r = client.post("/api/auth/login", json={
    "phone": "13800004002",
    "password": "UserPass123",
    "login_type": "password",
})
check("2.2 Warned user can still login", 200, r)

# ============================================================
# Phase 3: Multiple warnings
# ============================================================
print("\n=== Phase 3: Multiple warnings ===")

r = client.post(f"/api/admin/users/{TARGET_ID}/ban", json={
    "action": "warn",
    "reason": "重复违规",
}, headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
check("3.1 Second warn → warn_count=2", 200, r, lambda j: j["data"]["warn_count"] == 2)

r = client.post(f"/api/admin/users/{TARGET_ID}/ban", json={
    "action": "warn",
    "reason": "第三次警告",
}, headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
check("3.2 Third warn → warn_count=3", 200, r, lambda j: j["data"]["warn_count"] == 3)

# ============================================================
# Phase 4: Warn notification check
# ============================================================
print("\n=== Phase 4: Notification check ===")

r = client.get("/api/notifications", headers={"Authorization": f"Bearer {TARGET_TOKEN}"})
check("4.1 Target user has warning notifications", 200, r, lambda j: (
    j["data"]["total"] >= 3
))

# ============================================================
# Phase 5: Non-admin cannot warn
# ============================================================
print("\n=== Phase 5: Permission check ===")

r = client.post(f"/api/admin/users/{TARGET_ID}/ban", json={
    "action": "warn",
    "reason": "普通用户越权",
}, headers={"Authorization": f"Bearer {USER_TOKEN}"})
check("5.1 Non-admin warn → 403", 403, r)

# ============================================================
# Phase 6: Cannot warn/bann oneself
# ============================================================
print("\n=== Phase 6: Self-operate check ===")

r = client.post(f"/api/admin/users/{ADMIN_USER_ID}/ban", json={
    "action": "warn",
    "reason": "不能警告自己",
}, headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
check("6.1 Admin warn self → 400", 400, r)

# ============================================================
# Phase 7: Ban/unban still works alongside warn
# ============================================================
print("\n=== Phase 7: Ban/unban unaffected ===")

r = client.post(f"/api/admin/users/{TARGET_ID}/ban", json={
    "action": "ban",
    "reason": "多次违规后封禁",
    "duration_hours": 24,
}, headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
check("7.1 Ban after warns", 200, r, lambda j: j["data"]["status"] == "disabled")

r = client.post("/api/auth/login", json={
    "phone": "13800004002",
    "password": "UserPass123",
    "login_type": "password",
})
check("7.2 Banned user login → 401", 401, r)

r = client.post(f"/api/admin/users/{TARGET_ID}/ban", json={
    "action": "unban",
    "reason": "已改正",
}, headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
check("7.3 Unban user", 200, r, lambda j: j["data"]["status"] == "active")

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
