"""Market data API integration tests. Covers spec section 2.7.

Endpoints: /market/indices, /market/kline/{secid}

External API calls (EastMoney/Sina) may fail in test environment.
Tests accept graceful degradation (200 empty or 500) for network failures.

Run:  cd backend && python tests/test_market_api.py
"""

import gc
import os
import sys
import time
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite:///./test_market.db"
DB_PATH = Path("test_market.db")
DB_PATH.unlink(missing_ok=True)

import app.models  # noqa: F401
from app.db.base import Base
from app.db.session import engine

Base.metadata.create_all(bind=engine)

from fastapi.testclient import TestClient
from app.main import app

passed = 0
failed = 0


def check(label, expect, response, allow_codes=None, show_key=None):
    """Check response. allow_codes is a tuple of acceptable status codes
    for calls that depend on external APIs (network may fail)."""
    global passed, failed
    try:
        j = response.json()
    except Exception:
        j = {"detail": "(non-JSON body)"}
    acceptable = allow_codes if allow_codes else (expect,)
    ok = response.status_code in acceptable
    if ok:
        passed += 1
        marker = "OK"
    else:
        failed += 1
        marker = "FAIL"
    msg = j.get("message", j.get("detail", ""))
    print(f"{marker} | {label}: HTTP {response.status_code} | {msg}")
    if not ok:
        print(f"     EXPECTED one of {acceptable}, GOT {response.status_code}")
        print(f"     Full response: {j}")
    if show_key and ok and "data" in j:
        d = j["data"]
        if isinstance(d, dict) and show_key in d:
            print(f"     {show_key}={d[show_key]}")
    return j


def run():
    with TestClient(app) as client:
        # ══════════════════════════════════════════════════════════════
        # 1. Indices
        # ══════════════════════════════════════════════════════════════
        r = client.get("/api/market/indices")
        j = check("1.1 获取指数行情", 200, r, allow_codes=(200, 500))
        if r.status_code == 200:
            data = j["data"]
            assert isinstance(data, list), f"expected list, got {type(data)}"
            if data:
                idx = data[0]
                assert "code" in idx and "name" in idx, f"missing fields: {idx.keys()}"
                assert "price" in idx or idx.get("price") is None
                print(f"     idx={idx.get('code')} name={idx.get('name')} price={idx.get('price')}")
            else:
                print("     (empty — external API may be unavailable)")

        # ══════════════════════════════════════════════════════════════
        # 2. K-line
        # ══════════════════════════════════════════════════════════════
        r = client.get("/api/market/kline/1.000001", params={"klt": 101})
        j = check("2.1 日K线(daily)", 200, r, allow_codes=(200, 500))
        if r.status_code == 200:
            data = j["data"]
            if data:
                candle = data[0]
                assert "date" in candle, f"missing date: {candle}"
                assert "open" in candle and "close" in candle
                print(f"     date={candle['date']} close={candle.get('close')}")

        r = client.get("/api/market/kline/1.000001", params={"klt": 102})
        check("2.2 周K线(weekly)", 200, r, allow_codes=(200, 500))

        r = client.get("/api/market/kline/1.000001", params={"klt": 103})
        check("2.3 月K线(monthly)", 200, r, allow_codes=(200, 500))

        r = client.get("/api/market/kline/1.000001", params={"klt": 5})
        check("2.4 5分钟K线", 200, r, allow_codes=(200, 500))

        r = client.get("/api/market/kline/9.999999")
        check("2.5 无效secid", 200, r, allow_codes=(200, 404, 500))
        # May return 200 empty, 404, or 500 depending on external API response

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
    print(f"\n{'='*60}")
    print(f"RESULTS: {passed} passed, {failed} failed")
    print(f"{'='*60}")
    sys.exit(exit_code)
