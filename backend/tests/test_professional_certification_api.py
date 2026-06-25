"""Professional certification API tests — submit, admin review list, approve/reject.

Run:  cd backend && python tests/test_professional_certification_api.py
"""
import gc
import os
import pathlib
import sys
import time

os.environ["DATABASE_URL"] = "sqlite:///./test_prof_cert.db"

DB_PATH = pathlib.Path("test_prof_cert.db")
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
    "phone": "13800005001",
    "password": "AdminPass123",
    "nickname": "prof_admin",
})
check("1.1 Register admin", 201, r)
ADMIN_TOKEN = r.json()["data"]["token"]

from app.db.session import SessionLocal
from app.models.user import User, UserRole

db_session = SessionLocal()
db_session.query(User).filter(User.phone == "13800005001").update({"role": UserRole.ADMIN})
db_session.commit()

r = client.post("/api/auth/register", json={
    "phone": "13800005002",
    "password": "UserPass123",
    "nickname": "prof_applicant",
})
check("1.2 Register applicant", 201, r)
USER_TOKEN = r.json()["data"]["token"]
USER_ID = r.json()["data"]["user"]["id"]

# Normal user (non-admin, not applicant)
r = client.post("/api/auth/register", json={
    "phone": "13800005003",
    "password": "UserPass123",
    "nickname": "other_user",
})
check("1.3 Register other user", 201, r)
OTHER_TOKEN = r.json()["data"]["token"]

db_session.close()

# ============================================================
# Phase 2: Submit professional certification
# ============================================================
print("\n=== Phase 2: Submit professional certification ===")

r = client.post("/api/auth/professional-certification", json={
    "qualification_docs": [
        {"name": "证券从业资格证", "url": "/uploads/cert1.pdf"},
        {"name": "学历证明", "url": "/uploads/degree.pdf"},
    ],
    "description": "具有5年证券从业经验",
}, headers={"Authorization": f"Bearer {USER_TOKEN}"})
check("2.1 Submit professional certification", 200, r, lambda j: (
    j["data"]["status"] == "pending"
    and "certification_id" in j["data"]
))

# Duplicate pending submission
r = client.post("/api/auth/professional-certification", json={
    "qualification_docs": [
        {"name": "另一份证书", "url": "/uploads/other.pdf"},
    ],
}, headers={"Authorization": f"Bearer {USER_TOKEN}"})
check("2.2 Duplicate pending submission → 409", 409, r)

# Submit without auth
r = client.post("/api/auth/professional-certification", json={
    "qualification_docs": [{"name": "证", "url": "/uploads/c.pdf"}],
})
check("2.3 Submit without auth → 403", 403, r)

# ============================================================
# Phase 3: Admin reviews certification
# ============================================================
print("\n=== Phase 3: Admin review ===")

# List pending certifications
r = client.get("/api/admin/professional-certifications?status=pending",
               headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
check("3.1 List pending certifications", 200, r, lambda j: (
    len(j["data"]) >= 1
))
CERT_ID = r.json()["data"][0]["id"]

# Approve certification
r = client.post(f"/api/admin/professional-certifications/{CERT_ID}/review", json={
    "action": "approve",
    "comment": "审核通过，符合专业认证条件",
}, headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
check("3.2 Approve certification", 200, r)

# Verify user is now professional
r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {USER_TOKEN}"})
check("3.3 User is now professional (加V)", 200, r, lambda j: (
    j["data"]["is_professional"] is True
    and j["data"]["auth_level"] == "professional"
))

# Non-admin cannot review
r = client.post(f"/api/admin/professional-certifications/{CERT_ID}/review", json={
    "action": "approve",
}, headers={"Authorization": f"Bearer {OTHER_TOKEN}"})
check("3.4 Non-admin review → 403", 403, r)

# ============================================================
# Phase 4: Submit another and reject
# ============================================================
print("\n=== Phase 4: Reject flow ===")

# Create another user to submit
r = client.post("/api/auth/register", json={
    "phone": "13800005004",
    "password": "UserPass123",
    "nickname": "reject_applicant",
})
check("4.1 Register another applicant", 201, r)
USER2_TOKEN = r.json()["data"]["token"]

r = client.post("/api/auth/professional-certification", json={
    "qualification_docs": [
        {"name": "假证书", "url": "/uploads/fake.pdf"},
    ],
}, headers={"Authorization": f"Bearer {USER2_TOKEN}"})
check("4.2 Submit certification", 200, r)
CERT2_ID = r.json()["data"]["certification_id"]

r = client.post(f"/api/admin/professional-certifications/{CERT2_ID}/review", json={
    "action": "reject",
    "comment": "资质证明不充分",
}, headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
check("4.3 Reject certification", 200, r)

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
