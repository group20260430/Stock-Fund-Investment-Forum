"""Admin mute API tests — mute/unmute flow, post/comment restriction.

Run:  cd backend && python tests/test_admin_mute_api.py
"""
import gc
import os
import pathlib
import sys
import time

os.environ["DATABASE_URL"] = "sqlite:///./test_admin_mute.db"

DB_PATH = pathlib.Path("test_admin_mute.db")
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


def get_token(label, phone, pwd, nickname):
    r = client.post("/api/auth/register", json={"phone": phone, "password": pwd, "nickname": nickname})
    check(label, 201, r)
    return r.json()["data"]["token"], r.json()["data"]["user"]["id"]


# ============================================================
# Phase 1: Setup
# ============================================================
print("\n=== Phase 1: Setup ===")

ADMIN_TOKEN, _ = get_token("1.1 Register admin", "13800009001", "AdminPass123", "admin_mute")

from app.db.session import SessionLocal
from app.models.user import User, UserRole
from app.models.content import Category

db_session = SessionLocal()
db_session.query(User).filter(User.phone == "13800009001").update({"role": UserRole.ADMIN})
cat = Category(name="测试板块", description="for tests", sort_order=1)
db_session.add(cat)
db_session.commit()
CAT_ID = cat.id
ADMIN_USER_ID = db_session.query(User).filter(User.phone == "13800009001").first().id
db_session.close()

TARGET_TOKEN, TARGET_ID = get_token("1.2 Register target", "13800009002", "UserPass123", "mute_target")
USER_TOKEN, _ = get_token("1.3 Register normal", "13800009003", "UserPass123", "normal_user")

# ============================================================
# Phase 2: Admin mutes user
# ============================================================
print("\n=== Phase 2: Admin mute ===")

r = client.post(f"/api/admin/users/{TARGET_ID}/ban", json={
    "action": "mute", "reason": "频繁发布广告", "duration_hours": 24,
}, headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
check("2.1 Admin mute user (24h)", 200, r, lambda j: j["data"]["status"] == "silenced")

# Muted user can still login
r = client.post("/api/auth/login", json={
    "phone": "13800009002", "password": "UserPass123", "login_type": "password",
})
check("2.2 Muted user can still login", 200, r)

# ============================================================
# Phase 3: Muted user cannot create post
# ============================================================
print("\n=== Phase 3: Post restriction ===")

r = client.post("/api/posts", json={
    "title": "测试帖子", "content": "被禁言用户试图发帖",
    "category_id": CAT_ID, "post_type": "normal",
}, headers={"Authorization": f"Bearer {TARGET_TOKEN}"})
check("3.1 Muted user cannot create post → 403", 403, r)

# Normal user can still post
r = client.post("/api/posts", json={
    "title": "正常帖子", "content": "普通用户发帖",
    "category_id": CAT_ID, "post_type": "normal",
}, headers={"Authorization": f"Bearer {USER_TOKEN}"})
check("3.2 Normal user creates post", 201, r)
POST_ID = r.json()["data"]["id"]

# ============================================================
# Phase 4: Muted user cannot comment
# ============================================================
print("\n=== Phase 4: Comment restriction ===")

r = client.post(f"/api/posts/{POST_ID}/comments", json={
    "content": "被禁言用户试图评论",
}, headers={"Authorization": f"Bearer {TARGET_TOKEN}"})
check("4.1 Muted user cannot comment → 403", 403, r)

# Normal user can still comment
r = client.post(f"/api/posts/{POST_ID}/comments", json={
    "content": "正常用户的评论",
}, headers={"Authorization": f"Bearer {USER_TOKEN}"})
check("4.2 Normal user can still comment", 201, r)

# ============================================================
# Phase 5: Admin unmutes user
# ============================================================
print("\n=== Phase 5: Admin unmute ===")

r = client.post(f"/api/admin/users/{TARGET_ID}/ban", json={
    "action": "unmute",
}, headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
check("5.1 Admin unmute user", 200, r, lambda j: j["data"]["status"] == "active")

# Unmuted user can post again
r = client.post("/api/posts", json={
    "title": "解禁后发帖", "content": "禁言解除后可以正常发帖了",
    "category_id": CAT_ID, "post_type": "normal",
}, headers={"Authorization": f"Bearer {TARGET_TOKEN}"})
check("5.2 Unmuted user can post again", 201, r)

# Unmuted user can comment again
r = client.post(f"/api/posts/{POST_ID}/comments", json={
    "content": "解禁后可以评论了",
}, headers={"Authorization": f"Bearer {TARGET_TOKEN}"})
check("5.3 Unmuted user can comment again", 201, r)

# ============================================================
# Phase 6: Permission checks
# ============================================================
print("\n=== Phase 6: Permission checks ===")

r = client.post(f"/api/admin/users/{TARGET_ID}/ban", json={
    "action": "mute", "reason": "越权",
}, headers={"Authorization": f"Bearer {USER_TOKEN}"})
check("6.1 Non-admin mute → 403", 403, r)

r = client.post(f"/api/admin/users/{ADMIN_USER_ID}/ban", json={
    "action": "mute", "reason": "不能禁言自己",
}, headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
check("6.2 Admin mute self → 400", 400, r)

# ============================================================
# Phase 7: Check mute notification
# ============================================================
print("\n=== Phase 7: Notification check ===")

r = client.get("/api/notifications",
               headers={"Authorization": f"Bearer {TARGET_TOKEN}"})
check("7.1 Mute notification received", 200, r, lambda j: j["data"]["total"] >= 1)

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
