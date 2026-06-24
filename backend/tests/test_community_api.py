"""Community / Groups / Messages API tests. Covers spec section 2.5.

Run:  cd backend && python tests/test_community_api.py
"""

import gc
import os
import sys
import time
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite:///./test_community.db"
DB_PATH = Path("test_community.db")
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
        "phone": phone, "password": "Community123", "nickname": nickname,
    })
    assert r.status_code == 201, r.text
    d = r.json()["data"]
    return d["user_id"], {"Authorization": f"Bearer {d['token']}"}


def run():
    with TestClient(app) as client:
        owner_id, owner_h = register(client, "13800004001", "Owner")
        member_id, member_h = register(client, "13800004002", "Member")
        third_id, third_h = register(client, "13800004003", "Third")

        # ══════════════════════════════════════════════════════════════
        # 1. Group creation
        # ══════════════════════════════════════════════════════════════
        r = client.post("/api/groups", headers=owner_h, json={
            "name": "价值投资群", "description": "讨论长期投资", "need_approval": True,
        })
        j = check("1.1 创建群组(需审批)", 201, r, "id")
        group_id = j["data"]["id"]

        r = client.post("/api/groups", headers=owner_h, json={
            "name": "价值投资群", "description": "重复",
        })
        check("1.2 重名群组", 409, r)

        r = client.post("/api/groups", json={
            "name": "未登录群", "description": "x",
        })
        check("1.3 未登录创建群组", 403, r)

        r = client.post("/api/groups", headers=owner_h, json={
            "name": "", "description": "x",
        })
        check("1.4 名称为空", 422, r)

        # ══════════════════════════════════════════════════════════════
        # 2. Group list
        # ══════════════════════════════════════════════════════════════
        r = client.get("/api/groups", params={"type": "explore"})
        check("2.1 发现群组(explore)", 200, r)

        r = client.get("/api/groups", params={"type": "my"}, headers=owner_h)
        check("2.2 我的群组(my)", 200, r)

        r = client.get("/api/groups", params={"type": "joined"}, headers=owner_h)
        check("2.3 已加入群组(joined)", 200, r)

        # ══════════════════════════════════════════════════════════════
        # 3. Join group
        # ══════════════════════════════════════════════════════════════
        r = client.post(f"/api/groups/{group_id}/join", headers=member_h)
        j = check("3.1 加入需审批群组(pending)", 200, r)
        assert j["data"]["status"] == "pending"

        # Create a public group with no approval
        r = client.post("/api/groups", headers=owner_h, json={
            "name": "公开群", "description": "直接加入", "need_approval": False,
        })
        pub_id = r.json()["data"]["id"]
        r = client.post(f"/api/groups/{pub_id}/join", headers=third_h)
        j = check("3.2 加入公开群(直接加入)", 200, r)
        assert j["data"]["status"] == "approved"

        # Already a member → re-join
        r = client.post(f"/api/groups/{pub_id}/join", headers=third_h)
        j = check("3.3 已是成员再次加入", 200, r)
        assert j["data"]["status"] == "approved"

        # Leave then rejoin
        client.post(f"/api/groups/{pub_id}/leave", headers=third_h)
        r = client.post(f"/api/groups/{pub_id}/join", headers=third_h)
        check("3.4 退出后重新加入", 200, r)

        # ══════════════════════════════════════════════════════════════
        # 4. Member review
        # ══════════════════════════════════════════════════════════════
        r = client.post(f"/api/groups/{group_id}/members/approve", headers=owner_h, json={
            "user_id": member_id, "action": "approve",
        })
        j = check("4.1 审核通过", 200, r)
        assert j["data"]["status"] == "approved"

        r = client.post(f"/api/groups/{group_id}/members/approve", headers=owner_h, json={
            "user_id": member_id, "action": "approve",
        })
        check("4.2 重复审核(已处理)", 400, r)

        # Reject: register a 4th user and reject
        fth_id, fth_h = register(client, "13800004004", "Fourth")
        client.post(f"/api/groups/{group_id}/join", headers=fth_h)
        r = client.post(f"/api/groups/{group_id}/members/approve", headers=owner_h, json={
            "user_id": fth_id, "action": "reject",
        })
        j = check("4.3 审核拒绝", 200, r)
        assert j["data"]["status"] == "rejected"

        # ══════════════════════════════════════════════════════════════
        # 5. Group detail
        # ══════════════════════════════════════════════════════════════
        r = client.get(f"/api/groups/{group_id}", headers=member_h)
        j = check("5.1 成员查看群组详情", 200, r)
        assert j["data"]["member_count"] >= 2

        r = client.get(f"/api/groups/{pub_id}", headers=third_h)
        check("5.2 非成员查看公开群", 200, r)

        # Private group
        r = client.post("/api/groups", headers=owner_h, json={
            "name": "私密群", "description": "私密", "visibility": "private",
        })
        priv_id = r.json()["data"]["id"]
        r = client.get(f"/api/groups/{priv_id}", headers=third_h)
        check("5.3 非成员查看私密群", 403, r)

        r = client.get("/api/groups/99999")
        check("5.4 群组不存在", 404, r)

        # ══════════════════════════════════════════════════════════════
        # 6. Group posts
        # ══════════════════════════════════════════════════════════════
        r = client.post(f"/api/groups/{group_id}/posts", headers=member_h, json={
            "title": "群内分享", "content": "群内帖子内容",
        })
        check("6.1 成员发群帖", 201, r)

        r = client.get(f"/api/groups/{group_id}/posts", headers=member_h)
        j = check("6.2 查看群帖列表", 200, r)
        assert j["data"]["total"] >= 1

        r = client.get(f"/api/groups/{group_id}/posts", headers=third_h)
        check("6.3 非成员查看群帖", 403, r)

        # ══════════════════════════════════════════════════════════════
        # 7. Edit group
        # ══════════════════════════════════════════════════════════════
        r = client.put(f"/api/groups/{group_id}", headers=owner_h, json={
            "description": "更新后的描述", "need_approval": False,
        })
        j = check("7.1 群主编辑群组", 200, r)
        assert j["data"]["description"] == "更新后的描述"

        r = client.put(f"/api/groups/{group_id}", headers=member_h, json={
            "description": "不应该成功",
        })
        check("7.2 成员编辑群组", 403, r)

        # ══════════════════════════════════════════════════════════════
        # 8. Messages — DM
        # ══════════════════════════════════════════════════════════════
        r = client.post("/api/messages", headers=owner_h, json={
            "receiver_id": member_id, "content": "欢迎加入群组",
        })
        check("8.1 发送私信", 201, r)

        r = client.get("/api/messages", headers=member_h)
        j = check("8.2 私信对话列表", 200, r)
        assert len(j["data"]["items"]) >= 1

        r = client.get("/api/messages", headers=member_h, params={
            "other_user_id": owner_id,
        })
        j = check("8.3 私信对话详情", 200, r)
        msg_id = j["data"]["items"][0]["id"]

        r = client.delete(f"/api/messages/{msg_id}", headers=member_h)
        check("8.4 非发送者删除私信", 403, r)

        r = client.delete(f"/api/messages/{msg_id}", headers=owner_h)
        check("8.5 发送者删除私信", 200, r)

        r = client.delete(f"/api/messages/{msg_id}", headers=owner_h)
        check("8.6 删除已删除消息", 404, r)

        r = client.post("/api/messages", headers=owner_h, json={
            "receiver_id": owner_id, "content": "发给自己",
        })
        check("8.7 自发送私信", 400, r)

        r = client.post("/api/messages", headers=owner_h, json={
            "receiver_id": 99999, "content": "hello",
        })
        check("8.8 向不存在用户发私信", 404, r)

        # ══════════════════════════════════════════════════════════════
        # 9. Messages — DM privacy
        # ══════════════════════════════════════════════════════════════
        # Set member's message_permission to followers_only via DB
        # (PUT endpoint has SQLAlchemy JSON tracking issue)
        db = SessionLocal()
        from app.models.user import User
        member_db = db.query(User).filter(User.id == member_id).first()
        member_db.privacy_settings = {
            "profile_visibility": "public",
            "message_permission": "followers_only",
            "show_investment_info": True,
            "show_follow_lists": True,
            "show_activity_status": True,
        }
        db.commit()
        db.close()
        # Third does NOT follow member → should be blocked
        r = client.post("/api/messages", headers=third_h, json={
            "receiver_id": member_id, "content": "隐私测试",
        })
        check("9.1 向非关注者发私信(隐私限制)", 403, r)

        # Reset member's privacy
        db = SessionLocal()
        member_db = db.query(User).filter(User.id == member_id).first()
        member_db.privacy_settings = {
            "profile_visibility": "public",
            "message_permission": "everyone",
            "show_investment_info": True,
            "show_follow_lists": True,
            "show_activity_status": True,
        }
        db.commit()
        db.close()

        # ══════════════════════════════════════════════════════════════
        # 10. Messages — group chat
        # ══════════════════════════════════════════════════════════════
        r = client.post("/api/messages", headers=member_h, json={
            "group_id": group_id, "content": "群聊消息测试",
        })
        check("10.1 发送群聊消息", 201, r)

        r = client.post("/api/messages", headers=third_h, json={
            "group_id": group_id, "content": "我不是成员",
        })
        check("10.2 非成员发送群消息", 403, r)

        r = client.get("/api/messages", headers=member_h, params={
            "group_id": group_id,
        })
        j = check("10.3 查看群消息列表", 200, r)
        assert j["data"]["total"] >= 1

        r = client.get("/api/messages", headers=third_h, params={
            "group_id": group_id,
        })
        check("10.4 非成员查看群消息", 403, r)

        r = client.post("/api/messages", headers=owner_h, json={
            "receiver_id": member_id, "group_id": group_id, "content": "冲突",
        })
        check("10.5 同时指定receiver和group", 422, r)

        r = client.post("/api/messages", headers=member_h, json={
            "content": "没有目标",
        })
        check("10.6 未指定目标", 422, r)

        # ══════════════════════════════════════════════════════════════
        # 11. Leave / Remove / Dissolve
        # ══════════════════════════════════════════════════════════════
        # Join third to group (auto-approved since need_approval changed to False)
        client.post(f"/api/groups/{group_id}/join", headers=third_h)
        r = client.post(f"/api/groups/{group_id}/leave", headers=third_h)
        j = check("11.1 成员退出群组", 200, r)
        assert j["data"]["status"] == "left"

        r = client.post(f"/api/groups/{group_id}/leave", headers=owner_h)
        check("11.2 群主不能退出", 400, r)

        # Rejoin and kick
        client.post(f"/api/groups/{group_id}/join", headers=third_h)
        r = client.delete(f"/api/groups/{group_id}/members/{third_id}", headers=owner_h)
        check("11.3 群主移出成员", 200, r)

        r = client.delete(f"/api/groups/{group_id}/members/{owner_id}", headers=owner_h)
        check("11.4 不能移出群主", 400, r)

        r = client.delete(f"/api/groups/{group_id}/members/{third_id}", headers=member_h)
        check("11.5 非管理员移出成员", 403, r)

        r = client.delete(f"/api/groups/{group_id}", headers=member_h)
        check("11.6 非群主解散群组", 403, r)

        r = client.delete(f"/api/groups/{group_id}", headers=owner_h)
        check("11.7 群主解散群组", 200, r)

        r = client.get(f"/api/groups/{group_id}")
        check("11.8 已解散群组返回404", 404, r)

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
