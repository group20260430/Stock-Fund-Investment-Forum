"""Private message API tests — image and file message types.

Run:  cd backend && python tests/test_message_types_api.py
"""
import gc
import os
import pathlib
import sys
import time

os.environ["DATABASE_URL"] = "sqlite:///./test_message_types.db"

DB_PATH = pathlib.Path("test_message_types.db")
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
    "phone": "13800008001", "password": "UserPass123", "nickname": "msg_sender",
})
check("1.1 Register sender", 201, r)
SENDER_TOKEN = r.json()["data"]["token"]
SENDER_ID = r.json()["data"]["user"]["id"]

r = client.post("/api/auth/register", json={
    "phone": "13800008002", "password": "UserPass123", "nickname": "msg_receiver",
})
check("1.2 Register receiver", 201, r)
RECEIVER_TOKEN = r.json()["data"]["token"]
RECEIVER_ID = r.json()["data"]["user"]["id"]

# Sender follows receiver so message permission works
r = client.post(f"/api/users/{RECEIVER_ID}/follow",
                headers={"Authorization": f"Bearer {SENDER_TOKEN}"})
check("1.3 Sender follows receiver", 200, r)

# Receiver follows sender
r = client.post(f"/api/users/{SENDER_ID}/follow",
                headers={"Authorization": f"Bearer {RECEIVER_TOKEN}"})
check("1.4 Receiver follows sender", 200, r)

# ============================================================
# Phase 2: Send text message
# ============================================================
print("\n=== Phase 2: Text message ===")

r = client.post("/api/messages", json={
    "receiver_id": RECEIVER_ID,
    "content": "你好，这是一条文本消息",
    "message_type": "text",
}, headers={"Authorization": f"Bearer {SENDER_TOKEN}"})
check("2.1 Send text message", 201, r)

# ============================================================
# Phase 3: Send image message
# ============================================================
print("\n=== Phase 3: Image message ===")

r = client.post("/api/messages", json={
    "receiver_id": RECEIVER_ID,
    "content": "看这张K线图",
    "message_type": "image",
    "attachment_url": "/uploads/kline_chart.png",
}, headers={"Authorization": f"Bearer {SENDER_TOKEN}"})
check("3.1 Send image message", 201, r)

# ============================================================
# Phase 4: Send file message
# ============================================================
print("\n=== Phase 4: File message ===")

r = client.post("/api/messages", json={
    "receiver_id": RECEIVER_ID,
    "content": "这是分析报告",
    "message_type": "file",
    "attachment_url": "/uploads/report.pdf",
}, headers={"Authorization": f"Bearer {SENDER_TOKEN}"})
check("4.1 Send file message", 201, r)

# ============================================================
# Phase 5: Image message without attachment_url
# ============================================================
print("\n=== Phase 5: Validation ===")

r = client.post("/api/messages", json={
    "receiver_id": RECEIVER_ID,
    "content": "图片消息",
    "message_type": "image",
    # missing attachment_url
}, headers={"Authorization": f"Bearer {SENDER_TOKEN}"})
check("5.1 Image without attachment", 422, r)

# ============================================================
# Phase 6: Verify messages in conversation
# ============================================================
print("\n=== Phase 6: Conversation check ===")

r = client.get(f"/api/messages?other_user_id={RECEIVER_ID}",
               headers={"Authorization": f"Bearer {SENDER_TOKEN}"})
check("6.1 Get conversation messages", 200, r, lambda j: (
    len(j["data"]) >= 3
))

# Check there are different message types
r = client.get("/api/messages",
               headers={"Authorization": f"Bearer {RECEIVER_TOKEN}"})
check("6.2 Receiver message list", 200, r, lambda j: (
    len(j["data"]) >= 1
))

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
