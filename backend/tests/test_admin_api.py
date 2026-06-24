"""Admin & report API tests. Covers spec sections 2.9 and report endpoint.

Run:  cd backend && python tests/test_admin_api.py
"""

import gc
import os
import sys
import time
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite:///./test_admin.db"
DB_PATH = Path("test_admin.db")
DB_PATH.unlink(missing_ok=True)

import app.models  # noqa: F401
from app.db.base import Base
from app.db.session import SessionLocal, engine

Base.metadata.create_all(bind=engine)

from unittest.mock import PropertyMock, patch
from app.core.config import Settings
_patch_smtp = patch.object(Settings, "smtp_configured", new_callable=PropertyMock)
_patch_smtp.start().return_value = False

from fastapi.testclient import TestClient
from app.main import app
from app.models.content import Post, PostStatus
from app.models.user import User, UserRole, UserStatus

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
        "phone": phone, "password": "AdminTest123", "nickname": nickname,
    })
    assert r.status_code == 201, r.text
    d = r.json()["data"]
    return d["user_id"], {"Authorization": f"Bearer {d['token']}"}


def run():
    with TestClient(app) as client:
        # ── Setup: admin + regular user ─────────────────────────────
        admin_id, admin_h = register(client, "13800006001", "Admin")
        user_id, user_h = register(client, "13800006002", "NormalUser")

        # Elevate admin to ADMIN role
        db = SessionLocal()
        admin = db.query(User).filter(User.id == admin_id).first()
        admin.role = UserRole.ADMIN
        db.commit()
        db.close()

        cat_id = client.get("/api/categories").json()["data"][0]["id"]

        # Create a post, set to REVIEWING
        r = client.post("/api/posts", headers=user_h, json={
            "category_id": cat_id, "title": "待审核帖子", "content": "需要管理员处理",
        })
        post_id = r.json()["data"]["id"]
        db = SessionLocal()
        db.query(Post).filter(Post.id == post_id).update({"status": PostStatus.REVIEWING})
        db.commit()
        db.close()

        # ══════════════════════════════════════════════════════════════
        # 1. Report
        # ══════════════════════════════════════════════════════════════
        r = client.post("/api/report", headers=admin_h, json={
            "target_type": "user", "target_id": user_id,
            "reason": "spam", "description": "测试举报",
        })
        j = check("1.1 提交举报", 201, r, "id")
        report_id = j["data"]["id"]

        r = client.post("/api/report", headers=admin_h, json={
            "target_type": "user", "target_id": user_id,
            "reason": "spam", "description": "重复举报",
        })
        check("1.2 重复举报", 409, r)

        r = client.post("/api/report", json={
            "target_type": "user", "target_id": user_id, "reason": "spam",
        })
        check("1.3 未登录举报", 403, r)

        # ══════════════════════════════════════════════════════════════
        # 2. Review queue + review
        # ══════════════════════════════════════════════════════════════
        r = client.get("/api/admin/review-queue", headers=admin_h)
        j = check("2.1 审核队列(管理员)", 200, r)
        assert j["data"]["total"] >= 1
        review_id = j["data"]["items"][0]["id"]

        r = client.post(f"/api/admin/review-queue/{review_id}/review", headers=admin_h, json={
            "action": "approve",
        })
        j = check("2.2 审核通过", 200, r)
        assert j["data"]["status"] == "published"

        # Reject: create another REVIEWING post
        r = client.post("/api/posts", headers=user_h, json={
            "category_id": cat_id, "title": "待拒绝帖子", "content": "内容违规",
        })
        post2_id = r.json()["data"]["id"]
        db = SessionLocal()
        db.query(Post).filter(Post.id == post2_id).update({"status": PostStatus.REVIEWING})
        db.commit()
        db.close()
        r = client.get("/api/admin/review-queue", headers=admin_h)
        review2_id = r.json()["data"]["items"][0]["id"]
        r = client.post(f"/api/admin/review-queue/{review2_id}/review", headers=admin_h, json={
            "action": "reject", "comment": "违规内容",
        })
        j = check("2.3 审核拒绝", 200, r)
        assert j["data"]["status"] == "rejected"

        r = client.get("/api/admin/review-queue", headers=user_h)
        check("2.4 非管理员查看审核队列", 403, r)

        # ══════════════════════════════════════════════════════════════
        # 3. User management
        # ══════════════════════════════════════════════════════════════
        r = client.get("/api/admin/users", headers=admin_h)
        j = check("3.1 用户列表(全部)", 200, r)
        assert j["data"]["total"] >= 2

        r = client.get("/api/admin/users", headers=admin_h, params={"keyword": "Normal"})
        j = check("3.2 用户列表(关键词搜索)", 200, r)
        if r.status_code == 200 and j["data"]["items"]:
            assert j["data"]["items"][0]["nickname"] == "NormalUser"

        r = client.get("/api/admin/users", headers=admin_h, params={"status": "disabled"})
        j = check("3.3 用户列表(按状态筛选)", 200, r)
        assert r.status_code == 200, r.text

        # ══════════════════════════════════════════════════════════════
        # 4. Ban / Unban
        # ══════════════════════════════════════════════════════════════
        r = client.post(f"/api/admin/users/{user_id}/ban", headers=admin_h, json={
            "action": "ban", "reason": "违规", "duration_hours": 24,
        })
        j = check("4.1 封禁用户", 200, r)
        assert j["data"]["status"] == "disabled"

        # Verify banned user cannot login
        r = client.post("/api/auth/login", json={
            "phone": "13800006002", "password": "AdminTest123", "login_type": "password",
        })
        check("4.2 封禁用户无法登录", 401, r)

        r = client.post(f"/api/admin/users/{user_id}/ban", headers=admin_h, json={
            "action": "unban",
        })
        j = check("4.3 解封用户", 200, r)
        assert j["data"]["status"] == "active"

        # ══════════════════════════════════════════════════════════════
        # 5. Reports listing + handle
        # ══════════════════════════════════════════════════════════════
        r = client.get("/api/admin/reports", headers=admin_h)
        j = check("5.1 举报列表", 200, r)
        assert j["data"]["total"] >= 1

        r = client.post(f"/api/admin/reports/{report_id}", headers=admin_h, json={
            "action": "resolve", "comment": "已处理",
        })
        j = check("5.2 处理举报(已解决)", 200, r)
        assert j["data"]["status"] == "resolved"

        # ══════════════════════════════════════════════════════════════
        # 6. Categories
        # ══════════════════════════════════════════════════════════════
        r = client.post("/api/admin/categories", headers=admin_h, json={
            "name": "管理测试板块", "description": "测试",
        })
        j = check("6.1 创建分类", 201, r, "id")

        # ══════════════════════════════════════════════════════════════
        # 7. Sensitive words
        # ══════════════════════════════════════════════════════════════
        r = client.post("/api/admin/sensitive-words", headers=admin_h, json={
            "word": "违规广告", "level": "review",
        })
        j = check("7.1 添加敏感词", 201, r, "id")
        word_id = j["data"]["id"]

        r = client.get("/api/admin/sensitive-words", headers=admin_h)
        check("7.2 敏感词列表", 200, r)

        r = client.delete(f"/api/admin/sensitive-words/{word_id}", headers=admin_h)
        check("7.3 删除敏感词", 204, r)

        # ══════════════════════════════════════════════════════════════
        # 8. Statistics
        # ══════════════════════════════════════════════════════════════
        r = client.get("/api/admin/stats/overview", headers=admin_h)
        j = check("8.1 数据总览", 200, r)
        assert r.status_code == 200, r.text

        r = client.get("/api/admin/stats/trend", headers=admin_h, params={"period": "daily"})
        check("8.2 趋势数据(日)", 200, r)

        r = client.get("/api/admin/stats/trend", headers=admin_h, params={"period": "weekly"})
        check("8.3 趋势数据(周)", 200, r)

        r = client.get("/api/admin/stats/trend", headers=admin_h, params={"period": "monthly"})
        check("8.4 趋势数据(月)", 200, r)

        r = client.get("/api/admin/stats/hot-topics", headers=admin_h)
        j = check("8.5 热门话题", 200, r)
        assert r.status_code == 200, r.text

        r = client.get("/api/admin/stats/engagement", headers=admin_h)
        j = check("8.6 参与度报告", 200, r)
        assert r.status_code == 200, r.text

        # ══════════════════════════════════════════════════════════════
        # 9. Activity logs
        # ══════════════════════════════════════════════════════════════
        r = client.get("/api/admin/activity-logs", headers=admin_h)
        j = check("9.1 活动日志", 200, r)
        assert j["data"]["total"] >= 1

        # ══════════════════════════════════════════════════════════════
        # 10. Auth: non-admin rejected
        # ══════════════════════════════════════════════════════════════
        r = client.get("/api/admin/users", headers=user_h)
        check("10.1 非管理员访问管理接口", 403, r)

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
