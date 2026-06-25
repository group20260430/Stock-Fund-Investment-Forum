"""Email authentication API tests — email register, verify, login, reset password.

Run:  cd backend && python tests/test_email_auth_api.py
"""
import os, pathlib, sys

os.environ["DATABASE_URL"] = "sqlite:///./test_email_auth.db"

DB_PATH = pathlib.Path("test_email_auth.db")
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
# Phase 1: Register user A (phone) + login for admin operations
# ============================================================
print("\n=== Phase 1: Setup users ===")

r = client.post("/api/auth/register", json={
    "phone": "13800001001",
    "password": "AdminPass123",
    "nickname": "email_test_admin",
})
check("1.1 Setup admin register", 201, r)
ADMIN_TOKEN = r.json()["data"]["token"]

# Promote to admin directly via SQL
from app.db.session import SessionLocal
from app.models.user import User, UserRole

db_session = SessionLocal()
db_session.query(User).filter(User.phone == "13800001001").update({"role": UserRole.ADMIN})
db_session.commit()
db_session.close()

r = client.post("/api/auth/register", json={
    "phone": "13800001002",
    "password": "UserPass123",
    "nickname": "email_test_user",
})
check("1.2 Setup normal user register", 201, r)
USER_TOKEN = r.json()["data"]["token"]

# ============================================================
# Phase 2: Email send-code
# ============================================================
print("\n=== Phase 2: Email send-code ===")

r = client.post("/api/auth/email/send-code", json={
    "email": "newuser@test.com",
    "type": "register",
})
check("2.1 Send code for register (new email)", 200, r, lambda j: (
    j["data"]["expire_in"] == 300
))

r = client.post("/api/auth/email/send-code", json={
    "email": "newuser@test.com",
    "type": "login",
})
check("2.2 Send code for login (not registered yet)", 404, r)

r = client.post("/api/auth/email/send-code", json={
    "email": "newuser@test.com",
    "type": "reset_password",
})
check("2.3 Send code for reset (not registered yet)", 404, r)

# ============================================================
# Phase 3: Verify code & register by email
# ============================================================
print("\n=== Phase 3: Email register ===")

# Inject dev code into store directly (since SMTP is not configured)
from app.services.user_service import VerificationCodeStore
import time as time_module

VerificationCodeStore.set("email:register:newuser@test.com", "666666", ttl_seconds=300)

r = client.post("/api/auth/email/verify-code", json={
    "email": "newuser@test.com",
    "code": "666666",
})
check("3.1 Verify email code", 200, r, lambda j: j["data"]["verified"] is True)

r = client.post("/api/auth/email/register", json={
    "email": "newuser@test.com",
    "password": "TestPass123",
    "nickname": "email_user",
})
check("3.2 Register by email", 201, r, lambda j: (
    j["data"]["token"] is not None
    and j["data"]["user"]["email"] == "newuser@test.com"
    and j["data"]["user"]["nickname"] == "email_user"
))
EMAIL_TOKEN = r.json()["data"]["token"]

# Duplicate email register — need to set verified marker again
VerificationCodeStore.set("email:verified:newuser@test.com", "1", ttl_seconds=600)
r = client.post("/api/auth/email/register", json={
    "email": "newuser@test.com",
    "password": "TestPass456",
})
check("3.3 Duplicate email → 409", 409, r)

# Register without verifying
r = client.post("/api/auth/email/register", json={
    "email": "unverified@test.com",
    "password": "TestPass789",
})
check("3.4 Register without verification → 400", 400, r)

# ============================================================
# Phase 4: Email login
# ============================================================
print("\n=== Phase 4: Email login ===")

r = client.post("/api/auth/login", json={
    "phone": "newuser@test.com",
    "password": "TestPass123",
    "login_type": "password",
})
check("4.1 Email password login", 200, r, lambda j: (
    j["data"]["token"] is not None
    and j["data"]["user"]["email"] == "newuser@test.com"
))

r = client.post("/api/auth/login", json={
    "phone": "newuser@test.com",
    "password": "WrongPass",
    "login_type": "password",
})
check("4.2 Email wrong password → 401", 401, r)

# Email code login
VerificationCodeStore.set("email:login:newuser@test.com", "888888", ttl_seconds=300)

r = client.post("/api/auth/login", json={
    "phone": "newuser@test.com",
    "code": "888888",
    "login_type": "code",
})
check("4.3 Email code login", 200, r, lambda j: j["data"]["token"] is not None)

r = client.post("/api/auth/login", json={
    "phone": "newuser@test.com",
    "code": "000000",
    "login_type": "code",
})
check("4.4 Email wrong code → 401", 401, r)

# ============================================================
# Phase 5: Get/update profile (verify email user profile)
# ============================================================
print("\n=== Phase 5: Email user profile ===")

r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {EMAIL_TOKEN}"})
check("5.1 Get profile (email user)", 200, r, lambda j: (
    j["data"]["email"] == "newuser@test.com"
    and j["data"]["nickname"] == "email_user"
))

r = client.put("/api/auth/profile", json={
    "investment_tags": ["A股", "基金"],
    "follow_markets": ["sh", "sz"],
}, headers={"Authorization": f"Bearer {EMAIL_TOKEN}"})
check("5.2 Update investment preferences", 200, r)

# ============================================================
# Cleanup
# ============================================================
print(f"\n{'='*50}")
print(f"RESULTS: {passed} passed, {failed} failed")
if errors:
    print(f"Errors:")
    for e in errors:
        print(f"  - {e}")

try:
    DB_PATH.unlink(missing_ok=True)
except PermissionError:
    pass

raise SystemExit(0 if failed == 0 else 1)
