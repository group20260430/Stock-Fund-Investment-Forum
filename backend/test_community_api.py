import os
import gc
import time
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite:///./test_community.db"
Path("test_community.db").unlink(missing_ok=True)

from fastapi.testclient import TestClient

from app.db.session import engine
from app.main import app


def register(client: TestClient, phone: str, nickname: str) -> tuple[int, dict[str, str]]:
    response = client.post(
        "/api/auth/register",
        json={"phone": phone, "password": "Community123", "nickname": nickname},
    )
    data = response.json()["data"]
    return data["user_id"], {"Authorization": f"Bearer {data['token']}"}


def run() -> None:
    with TestClient(app) as client:
        owner_id, owner_headers = register(client, "13800004001", "Owner")
        member_id, member_headers = register(client, "13800004002", "Member")
        third_id, third_headers = register(client, "13800004003", "Third")

        # --- 创建群组 ---
        created = client.post(
            "/api/groups",
            headers=owner_headers,
            json={"name": "价值投资群", "description": "讨论长期投资", "need_approval": True},
        )
        assert created.status_code == 201, created.text
        group_id = created.json()["data"]["id"]

        # --- 重名检测 ---
        dup = client.post(
            "/api/groups",
            headers=owner_headers,
            json={"name": "价值投资群", "description": "重复"},
        )
        assert dup.status_code == 409

        # --- 加入群组（需审批 → pending） ---
        joined = client.post(f"/api/groups/{group_id}/join", headers=member_headers)
        assert joined.json()["data"]["status"] == "pending"

        # --- 审核通过 ---
        approved = client.post(
            f"/api/groups/{group_id}/members/approve",
            headers=owner_headers,
            json={"user_id": member_id, "action": "approve"},
        )
        assert approved.status_code == 200 and approved.json()["data"]["status"] == "approved"

        # --- 重复审核应返回400（不再是404） ---
        dup_approve = client.post(
            f"/api/groups/{group_id}/members/approve",
            headers=owner_headers,
            json={"user_id": member_id, "action": "approve"},
        )
        assert dup_approve.status_code == 400  # 修复后为 400

        # --- 群组详情含 member_count ---
        group = client.get(f"/api/groups/{group_id}", headers=member_headers)
        assert group.status_code == 200 and group.json()["data"]["member_count"] == 2

        # --- 群内发帖 ---
        group_post = client.post(
            f"/api/groups/{group_id}/posts",
            headers=member_headers,
            json={"title": "群内分享", "content": "群内帖子内容"},
        )
        assert group_post.status_code == 201, group_post.text
        posts = client.get(f"/api/groups/{group_id}/posts", headers=member_headers)
        assert posts.status_code == 200 and posts.json()["data"]["total"] == 1

        # --- 非成员无法查看群帖 ---
        assert client.get(f"/api/groups/{group_id}/posts", headers=third_headers).status_code == 403

        # --- 编辑群组 ---
        updated = client.put(
            f"/api/groups/{group_id}",
            headers=owner_headers,
            json={"description": "更新后的描述", "need_approval": False},
        )
        assert updated.status_code == 200
        assert updated.json()["data"]["description"] == "更新后的描述"
        assert updated.json()["data"]["need_approval"] is False

        # --- 非管理员不能编辑 ---
        assert client.put(
            f"/api/groups/{group_id}",
            headers=member_headers,
            json={"description": "不应该成功"},
        ).status_code == 403

        # --- 发送私信 ---
        sent = client.post(
            "/api/messages",
            headers=owner_headers,
            json={"receiver_id": member_id, "content": "欢迎加入群组"},
        )
        assert sent.status_code == 201, sent.text

        # --- 私信对话列表（分组） ---
        conversations = client.get("/api/messages", headers=member_headers)
        assert conversations.status_code == 200
        conv_items = conversations.json()["data"]["items"]
        assert len(conv_items) >= 1
        assert conv_items[0]["other_user"]["id"] == owner_id

        # --- 私信对话详情 ---
        messages = client.get(
            "/api/messages", headers=member_headers, params={"other_user_id": owner_id}
        )
        assert messages.status_code == 200
        assert messages.json()["data"]["items"][0]["is_read"] is True

        # --- 删除私信 ---
        msg_id = messages.json()["data"]["items"][0]["id"]
        # 非发送者不能删除
        assert client.delete(f"/api/messages/{msg_id}", headers=member_headers).status_code == 403
        # 发送者可以删除
        del_resp = client.delete(f"/api/messages/{msg_id}", headers=owner_headers)
        assert del_resp.status_code == 200

        # --- 已删除的消息返回404 ---
        assert client.delete(f"/api/messages/{msg_id}", headers=owner_headers).status_code == 404

        # --- 通知：审核通过产生通知 ---
        notifs = client.get("/api/notifications", headers=member_headers)
        assert notifs.status_code == 200
        notif_types = [n["type"] for n in notifs.json()["data"]["items"]]
        assert "group_approved" in notif_types

        # --- 通知：私信产生通知 ---
        notifs = client.get("/api/notifications", headers=member_headers, params={"type": "new_message"})
        assert notifs.status_code == 200
        assert len(notifs.json()["data"]["items"]) >= 1

        # --- 通知类型筛选 ---
        follow_notifs = client.get("/api/notifications", headers=member_headers, params={"type": "follow"})
        assert follow_notifs.status_code == 200

        # --- 仅未读通知 ---
        unread_notifs = client.get("/api/notifications", headers=member_headers, params={"unread_only": "true"})
        assert unread_notifs.status_code == 200

        # --- 通知全部已读 ---
        mark_all = client.put("/api/notifications/read", headers=member_headers)
        assert mark_all.status_code == 200

        # --- 未读计数 ---
        count_resp = client.get("/api/notifications/unread-count", headers=member_headers)
        assert count_resp.status_code == 200
        assert count_resp.json()["data"]["unread_count"] == 0

        # --- 退出群组 ---
        # 先用第三个用户加入群组测试退出
        client.post(f"/api/groups/{group_id}/join", headers=third_headers)  # 自动审批
        leave_resp = client.post(f"/api/groups/{group_id}/leave", headers=third_headers)
        assert leave_resp.status_code == 200
        assert leave_resp.json()["data"]["status"] == "left"

        # --- 群主不能退出 ---
        assert client.post(f"/api/groups/{group_id}/leave", headers=owner_headers).status_code == 400

        # --- 踢出成员 ---
        # 重新加入 third
        client.post(f"/api/groups/{group_id}/join", headers=third_headers)
        kick_resp = client.delete(f"/api/groups/{group_id}/members/{third_id}", headers=owner_headers)
        assert kick_resp.status_code == 200

        # --- 不能踢群主 ---
        assert client.delete(f"/api/groups/{group_id}/members/{owner_id}", headers=owner_headers).status_code == 400

        # --- 非管理员不能踢人 ---
        assert client.delete(f"/api/groups/{group_id}/members/{third_id}", headers=member_headers).status_code == 403

        # --- 解散群组 ---
        # 非群主不能解散
        assert client.delete(f"/api/groups/{group_id}", headers=member_headers).status_code == 403
        # 群主解散
        del_group = client.delete(f"/api/groups/{group_id}", headers=owner_headers)
        assert del_group.status_code == 200

        # --- 已删除群组返回404 ---
        assert client.get(f"/api/groups/{group_id}").status_code == 404

        # --- 禁止自发送私信 ---
        assert client.post(
            "/api/messages",
            headers=owner_headers,
            json={"receiver_id": owner_id, "content": "发给自己"},
        ).status_code == 400

        # --- 向不存在用户发私信 ---
        assert client.post(
            "/api/messages",
            headers=owner_headers,
            json={"receiver_id": 99999, "content": "hello"},
        ).status_code == 404


def _cleanup_db(db_path: Path) -> None:
    engine.dispose()
    gc.collect()
    for attempt in range(3):
        try:
            db_path.unlink(missing_ok=True)
            return
        except PermissionError:
            if attempt == 2:
                print(f"WARNING | cleanup failed for {db_path.name}")
                return
            time.sleep(0.2)
            gc.collect()


if __name__ == "__main__":
    try:
        run()
        print("community API tests passed")
    finally:
        _cleanup_db(Path("test_community.db"))
