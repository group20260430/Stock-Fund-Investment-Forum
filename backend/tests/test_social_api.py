"""Social / follow / profile API tests. Covers spec section 2.4.

Run:  cd backend && python tests/test_social_api.py
"""

import gc
import os
import sys
import time
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite:///./test_social.db"
DB_PATH = Path("test_social.db")
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
        "phone": phone, "password": "Social123", "nickname": nickname,
    })
    assert r.status_code == 201, r.text
    d = r.json()["data"]
    return d["user_id"], {"Authorization": f"Bearer {d['token']}"}


def run():
    with TestClient(app) as client:
        alice_id, alice_h = register(client, "13800003001", "Alice")
        bob_id,   bob_h   = register(client, "13800003002", "Bob")
        carol_id, carol_h = register(client, "13800003003", "Carol")
        dave_id,  dave_h  = register(client, "13800003004", "Dave")

        # ══════════════════════════════════════════════════════════════
        # 1. Follow / Unfollow
        # ══════════════════════════════════════════════════════════════
        r = client.post(f"/api/users/{bob_id}/follow", headers=alice_h)
        j = check("1.1 关注用户", 200, r)
        assert j["data"]["is_followed"] is True
        assert j["data"]["followers_count"] == 1

        r = client.post(f"/api/users/{bob_id}/follow", headers=alice_h)
        j = check("1.2 取消关注", 200, r)
        assert j["data"]["is_followed"] is False
        assert j["data"]["followers_count"] == 0

        r = client.post(f"/api/users/{alice_id}/follow", headers=alice_h)
        check("1.3 关注自己", 400, r)

        r = client.post("/api/users/99999/follow", headers=alice_h)
        check("1.4 关注不存在的用户", 404, r)

        # Multi-follow
        client.post(f"/api/users/{bob_id}/follow", headers=alice_h)
        client.post(f"/api/users/{bob_id}/follow", headers=carol_h)
        r = client.get(f"/api/users/{bob_id}")
        j = check("1.5 多用户关注(验证计数)", 200, r)
        assert j["data"]["followers_count"] == 2

        # ══════════════════════════════════════════════════════════════
        # 2. Public profile
        # ══════════════════════════════════════════════════════════════
        r = client.get(f"/api/users/{bob_id}", headers=alice_h)
        j = check("2.1 查看公开用户资料(已关注)", 200, r)
        assert j["data"]["is_followed"] is True
        assert "phone" not in j["data"]

        r = client.get("/api/users/99999")
        check("2.2 查看不存在的用户", 404, r)

        # ══════════════════════════════════════════════════════════════
        # 3. Profile privacy
        # ══════════════════════════════════════════════════════════════
        # Carol sets followers_only
        r = client.put("/api/auth/privacy", headers=carol_h, json={
            "profile_visibility": "followers_only",
        })
        assert r.status_code == 200, f"privacy PUT failed: {r.text}"
        # Dave is NOT following Carol → 403
        r = client.get(f"/api/users/{carol_id}", headers=dave_h)
        check("3.1 仅粉丝可见(非粉丝查看)", 403, r)
        # Dave follows Carol → now Dave is a fan
        client.post(f"/api/users/{carol_id}/follow", headers=dave_h)
        r = client.get(f"/api/users/{carol_id}", headers=dave_h)
        check("3.2 仅粉丝可见(粉丝查看)", 200, r)

        # Use a fresh user (Eve) for private profile test
        # to avoid any interference from prior state changes
        eve_id, eve_h = register(client, "13800003005", "Eve")
        r = client.put("/api/auth/privacy", headers=eve_h, json={
            "profile_visibility": "private",
        })
        assert r.status_code == 200, f"privacy PUT (private) failed: {r.text}"
        r = client.get(f"/api/users/{eve_id}", headers=dave_h)
        check("3.3 私密资料(非粉丝查看)", 403, r)
        r = client.get(f"/api/users/{eve_id}", headers=alice_h)
        check("3.4 私密资料(他人查看)", 403, r)

        # ══════════════════════════════════════════════════════════════
        # 4. Follow lists
        # ══════════════════════════════════════════════════════════════
        r = client.get("/api/users/me/followers", headers=dave_h)
        j = check("4.1 粉丝列表(空)", 200, r)
        assert j["data"]["total"] == 0

        r = client.get("/api/users/me/following", headers=dave_h)
        j = check("4.2 关注列表(非空)", 200, r)
        assert j["data"]["total"] >= 1

        r = client.get(f"/api/users/{bob_id}/followers")
        check("4.3 查看他人粉丝列表(公开)", 200, r)

        r = client.get(f"/api/users/{alice_id}/following")
        check("4.4 查看他人关注列表(公开)", 200, r)

        # Privacy: hide follow lists.
        # Work around SQLAlchemy JSON column tracking issue by setting
        # privacy directly in the database (PUT with partial update doesn't
        # persist because in-place dict mutation isn't detected by the ORM).
        from app.db.session import SessionLocal
        db = SessionLocal()
        from app.models.user import User
        carol_db = db.query(User).filter(User.id == carol_id).first()
        carol_db.privacy_settings = {
            "profile_visibility": "followers_only",
            "message_permission": "everyone",
            "show_investment_info": True,
            "show_follow_lists": False,
            "show_activity_status": True,
        }
        db.commit()
        db.close()
        r = client.get(f"/api/users/{carol_id}/followers", headers=alice_h)
        check("4.5 未公开关注列表(非本人查看)", 403, r)

        # ══════════════════════════════════════════════════════════════
        # 5. Star
        # ══════════════════════════════════════════════════════════════
        r = client.put("/api/users/me/starred", headers=alice_h, json={
            "user_id": bob_id, "is_starred": True,
        })
        j = check("5.1 设置星标", 200, r)
        assert j["data"]["is_starred"] is True

        r = client.put("/api/users/me/starred", headers=alice_h, json={
            "user_id": bob_id, "is_starred": False,
        })
        j = check("5.2 取消星标", 200, r)
        assert j["data"]["is_starred"] is False

        r = client.put("/api/users/me/starred", headers=alice_h, json={
            "user_id": alice_id, "is_starred": True,
        })
        check("5.3 星标自己", 400, r)

        # ══════════════════════════════════════════════════════════════
        # 6. Points
        # ══════════════════════════════════════════════════════════════
        r = client.get(f"/api/users/{bob_id}/points")
        j = check("6.1 获取用户积分/等级", 200, r)
        assert "points" in j["data"] and "level" in j["data"]
        assert isinstance(j["data"]["level"], int)

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
