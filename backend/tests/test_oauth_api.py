"""OAuth login API tests — QQ, WeChat, Weibo in dev mode.

All three providers use oauth_dev_mode=True so no real app credentials needed.

Run:  cd backend && python tests/test_oauth_api.py
"""
import gc
import os
import pathlib
import sys
import time

os.environ["DATABASE_URL"] = "sqlite:///./test_oauth.db"

DB_PATH = pathlib.Path("test_oauth.db")
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
# Phase 1: QQ OAuth login flow
# ============================================================
print("\n=== Phase 1: QQ OAuth ===")

# 1.1 Build authorize URL returns a redirect (307)
r = client.get("/api/auth/qq/login?redirect=/home", follow_redirects=False)
check("1.1 QQ authorize redirect", 307, r)
# Verify the Location header contains dev_qq_code
assert "dev_qq_code" in r.headers.get("location", ""), "Dev code not in redirect URL"

# 1.2 Simulate callback with dev code
r = client.get("/api/auth/qq/callback?code=dev_qq_code&state=", follow_redirects=False)
check("1.2 QQ callback (dev mode)", 307, r)
# Should redirect to frontend with token in fragment
loc = r.headers.get("location", "")
assert "token=" in loc, "No token in redirect URL"
assert "oauth/qq/callback" in loc, "Wrong frontend callback URL"

# 1.3 QQ callback without code → 422 (FastAPI auto-422 for missing Query with no default)
r = client.get("/api/auth/qq/callback")
check("1.3 QQ callback without code → 400", 400, r)

# 1.4 QQ callback with error → 400
r = client.get("/api/auth/qq/callback?error=access_denied")
check("1.4 QQ callback with error → 400", 400, r)

# ============================================================
# Phase 2: WeChat OAuth
# ============================================================
print("\n=== Phase 2: WeChat OAuth ===")

r = client.get("/api/auth/wechat/login?redirect=/profile", follow_redirects=False)
check("2.1 WeChat authorize redirect", 307, r)
assert "dev_auth_code" in r.headers.get("location", "")

r = client.get("/api/auth/wechat/callback?code=dev_auth_code&state=", follow_redirects=False)
check("2.2 WeChat callback (dev mode)", 307, r)
loc = r.headers.get("location", "")
assert "token=" in loc

r = client.get("/api/auth/wechat/callback")
check("2.3 WeChat callback without code → 400", 400, r)

r = client.get("/api/auth/wechat/callback?error=user_cancelled")
check("2.4 WeChat callback with error → 400", 400, r)

# ============================================================
# Phase 3: Weibo OAuth
# ============================================================
print("\n=== Phase 3: Weibo OAuth ===")

r = client.get("/api/auth/weibo/login?redirect=/settings", follow_redirects=False)
check("3.1 Weibo authorize redirect", 307, r)
assert "dev_weibo_code" in r.headers.get("location", "")

r = client.get("/api/auth/weibo/callback?code=dev_weibo_code&state=", follow_redirects=False)
check("3.2 Weibo callback (dev mode)", 307, r)
loc = r.headers.get("location", "")
assert "token=" in loc

r = client.get("/api/auth/weibo/callback")
check("3.3 Weibo callback without code → 400", 400, r)

r = client.get("/api/auth/weibo/callback?error=denied")
check("3.4 Weibo callback with error → 400", 400, r)

# ============================================================
# Phase 4: Verify users created in DB
# ============================================================
print("\n=== Phase 4: Verify OAuth users ===")

from app.db.session import SessionLocal
from app.models.oauth import OAuthAccount, OAuthProvider

db_session = SessionLocal()
qq_count = db_session.query(OAuthAccount).filter(OAuthAccount.provider == OAuthProvider.QQ).count()
wechat_count = db_session.query(OAuthAccount).filter(OAuthAccount.provider == OAuthProvider.WECHAT).count()
weibo_count = db_session.query(OAuthAccount).filter(OAuthAccount.provider == OAuthProvider.WEIBO).count()
db_session.close()

# Use pass/fail directly since check() expects a response object
if qq_count >= 1:
    print("  ✅ 4.1 QQ account created in DB")
    passed += 1
else:
    print("  ❌ 4.1 QQ account created in DB")
    failed += 1
    errors.append("No QQ OAuthAccount found")

if wechat_count >= 1:
    print("  ✅ 4.2 WeChat account created in DB")
    passed += 1
else:
    print("  ❌ 4.2 WeChat account created in DB")
    failed += 1
    errors.append("No WeChat OAuthAccount found")

if weibo_count >= 1:
    print("  ✅ 4.3 Weibo account created in DB")
    passed += 1
else:
    print("  ❌ 4.3 Weibo account created in DB")
    failed += 1
    errors.append("No Weibo OAuthAccount found")

# ============================================================
# Phase 5: Repeated login returns same user
# ============================================================
print("\n=== Phase 5: Repeated OAuth login ===")

r = client.get("/api/auth/qq/callback?code=dev_qq_code&state=", follow_redirects=False)
check("5.1 Repeated QQ callback", 307, r)

db_session = SessionLocal()
qq_count_after = db_session.query(OAuthAccount).filter(
    OAuthAccount.provider == OAuthProvider.QQ
).count()
db_session.close()

if qq_count_after == qq_count:
    print("  ✅ 5.2 Repeated login did not create duplicate account")
    passed += 1
else:
    print(f"  ❌ 5.2 Repeated login created duplicate (before={qq_count}, after={qq_count_after})")
    failed += 1
    errors.append(f"Duplicate QQ account created")

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
