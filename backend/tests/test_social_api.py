import os
import gc
import time
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite:///./test_social.db"
Path("test_social.db").unlink(missing_ok=True)

from fastapi.testclient import TestClient

from app.db.session import engine
from app.main import app


def register(client: TestClient, phone: str, nickname: str) -> tuple[int, dict[str, str]]:
    response = client.post(
        "/api/auth/register",
        json={"phone": phone, "password": "Social123", "nickname": nickname},
    )
    data = response.json()["data"]
    return data["user_id"], {"Authorization": f"Bearer {data['token']}"}


def run() -> None:
    with TestClient(app) as client:
        alice_id, alice_headers = register(client, "13800003001", "Alice")
        bob_id, bob_headers = register(client, "13800003002", "Bob")
        carol_id, carol_headers = register(client, "13800003003", "Carol")

        # --- 关注 ---
        followed = client.post(f"/api/users/{bob_id}/follow", headers=alice_headers)
        assert followed.status_code == 200, followed.text
        data = followed.json()["data"]
        assert data["is_followed"] is True
        assert data["followers_count"] == 1
        assert data["following_count"] == 1  # 修复后现在返回 following_count

        # --- 个人资料含 is_followed ---
        profile = client.get(f"/api/users/{bob_id}", headers=alice_headers)
        assert profile.status_code == 200
        assert profile.json()["data"]["is_followed"] is True
        assert "phone" not in profile.json()["data"]

        # --- 粉丝列表 ---
        followers = client.get(f"/api/users/{bob_id}/followers", headers=bob_headers)
        assert followers.json()["data"]["items"][0]["id"] == alice_id

        # --- 关注列表 ---
        following = client.get(f"/api/users/{alice_id}/following", headers=alice_headers)
        assert following.json()["data"]["items"][0]["id"] == bob_id

        # --- 星标用户 ---
        starred = client.put(
            "/api/users/me/starred",
            headers=alice_headers,
            json={"user_id": bob_id, "is_starred": True},
        )
        assert starred.status_code == 200 and starred.json()["data"]["is_starred"] is True
        assert client.get(f"/api/users/{bob_id}", headers=alice_headers).json()["data"]["is_starred"] is True

        # --- 取关 ---
        unfollowed = client.post(f"/api/users/{bob_id}/follow", headers=alice_headers)
        unfollowed_data = unfollowed.json()["data"]
        assert unfollowed_data["is_followed"] is False
        assert unfollowed_data["followers_count"] == 0
        assert unfollowed_data["following_count"] == 0  # 计数被正确减回

        # --- 禁止自关注 ---
        assert client.post(f"/api/users/{alice_id}/follow", headers=alice_headers).status_code == 400

        # --- 关注不存在的用户 ---
        assert client.post("/api/users/99999/follow", headers=alice_headers).status_code == 404

        # --- 多用户关注场景 ---
        client.post(f"/api/users/{bob_id}/follow", headers=alice_headers)
        client.post(f"/api/users/{bob_id}/follow", headers=carol_headers)
        bob_profile = client.get(f"/api/users/{bob_id}").json()["data"]
        assert bob_profile["followers_count"] == 2

        # --- 通知：关注产生通知 ---
        notifs = client.get("/api/notifications", headers=bob_headers)
        assert notifs.status_code == 200
        notif_types = [n["type"] for n in notifs.json()["data"]["items"]]
        assert "follow" in notif_types

        # --- 通知：标记已读 ---
        mark_resp = client.put("/api/notifications/read", headers=bob_headers)
        assert mark_resp.status_code == 200

        # --- 通知：未读计数 ---
        count_resp = client.get("/api/notifications/unread-count", headers=bob_headers)
        assert count_resp.status_code == 200
        assert count_resp.json()["data"]["unread_count"] == 0

        # --- 搜索用户结果含 is_followed ---
        search_resp = client.get("/api/search", params={"keyword": "Bob", "type": "user"}, headers=alice_headers)
        assert search_resp.status_code == 200
        search_users = search_resp.json()["data"]["items"]
        bob_found = [u for u in search_users if u["id"] == bob_id]
        assert len(bob_found) == 1
        assert bob_found[0]["is_followed"] is True  # 搜索结果显示关注状态

        # --- 分页粉丝列表 ---
        f1 = client.get(f"/api/users/{bob_id}/followers", params={"page": 1, "size": 1})
        assert f1.status_code == 200 and len(f1.json()["data"]["items"]) == 1
        assert f1.json()["data"]["total"] == 2

        # --- 匿名查看用户资料（不含 is_followed） ---
        anon_profile = client.get(f"/api/users/{bob_id}")
        assert anon_profile.status_code == 200
        assert anon_profile.json()["data"]["is_followed"] is False


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
        print("social API tests passed")
    finally:
        _cleanup_db(Path("test_social.db"))
