"""Notification API tests. Covers spec section 2.8.

Endpoints: list, mark-read, unread-count.

Run:  cd backend && python tests/test_notifications_api.py
"""

import gc
import os
import sys
import time
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite:///./test_notifications.db"
DB_PATH = Path("test_notifications.db")
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


def register(client, phone, nickname):
    r = client.post("/api/auth/register", json={
        "phone": phone, "password": "NotifTest1", "nickname": nickname,
    })
    assert r.status_code == 201, r.text
    d = r.json()["data"]
    return d["user_id"], {"Authorization": f"Bearer {d['token']}"}


def run():
    with TestClient(app) as client:
        # ── Setup ───────────────────────────────────────────────────
        alice_id, alice_h = register(client, "13800007001", "Alice")
        bob_id, bob_h = register(client, "13800007002", "Bob")

        # Alice follows Bob → generates FOLLOW notification for Bob
        client.post(f"/api/users/{bob_id}/follow", headers=alice_h)

        # ══════════════════════════════════════════════════════════════
        # 1. List notifications
        # ══════════════════════════════════════════════════════════════
        r = client.get("/api/notifications", headers=bob_h)
        j = check("1.1 全部通知", 200, r)
        assert r.status_code == 200, r.text
        assert j["data"]["total"] >= 1
        items = j["data"]["items"]
        assert any(n["type"] == "follow" for n in items), "expected follow notification"

        r = client.get("/api/notifications", headers=bob_h, params={"type": "follow"})
        j = check("1.2 按类型筛选(follow)", 200, r)
        assert j["data"]["total"] >= 1
        for n in j["data"]["items"]:
            assert n["type"] == "follow"

        r = client.get("/api/notifications", headers=bob_h, params={"unread_only": "true"})
        j = check("1.3 仅未读通知", 200, r)
        assert r.status_code == 200, r.text

        # New user with no notifications
        carol_id, carol_h = register(client, "13800007003", "Carol")
        r = client.get("/api/notifications", headers=carol_h)
        j = check("1.4 无通知用户", 200, r)
        assert r.status_code == 200, r.text
        assert j["data"]["total"] == 0

        # ══════════════════════════════════════════════════════════════
        # 2. Unread count
        # ══════════════════════════════════════════════════════════════
        r = client.get("/api/notifications/unread-count", headers=bob_h)
        j = check("2.1 未读数(有未读)", 200, r)
        assert j["data"]["unread_count"] >= 1

        # ══════════════════════════════════════════════════════════════
        # 3. Mark read
        # ══════════════════════════════════════════════════════════════
        # Mark single notification as read — body is raw JSON array
        notif_id = items[0]["id"]
        r = client.put("/api/notifications/read", headers=bob_h, json=[notif_id])
        j = check("3.1 标记单条已读", 200, r)
        assert r.status_code == 200, r.text
        assert j["data"]["marked_count"] == 1

        # Mark all as read — send empty body (no notification_ids param)
        r = client.put("/api/notifications/read", headers=bob_h)
        j = check("3.2 标记全部已读", 200, r)
        assert r.status_code == 200, r.text

        r = client.get("/api/notifications/unread-count", headers=bob_h)
        j = check("3.3 未读数(全部已读)", 200, r)
        assert j["data"]["unread_count"] == 0

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
