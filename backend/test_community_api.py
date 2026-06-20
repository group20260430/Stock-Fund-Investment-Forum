import os
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite:///./test_community.db"
Path("test_community.db").unlink(missing_ok=True)

from fastapi.testclient import TestClient

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
        category_id = client.get("/api/categories").json()["data"][0]["id"]

        created = client.post(
            "/api/groups",
            headers=owner_headers,
            json={"name": "价值投资群", "description": "讨论长期投资", "need_approval": True},
        )
        assert created.status_code == 201, created.text
        group_id = created.json()["data"]["id"]

        joined = client.post(f"/api/groups/{group_id}/join", headers=member_headers)
        assert joined.json()["data"]["status"] == "pending"
        approved = client.post(
            f"/api/groups/{group_id}/members/approve",
            headers=owner_headers,
            json={"user_id": member_id, "action": "approve"},
        )
        assert approved.status_code == 200 and approved.json()["data"]["status"] == "approved"

        group = client.get(f"/api/groups/{group_id}", headers=member_headers)
        assert group.status_code == 200 and group.json()["data"]["member_count"] == 2
        group_post = client.post(
            f"/api/groups/{group_id}/posts",
            headers=member_headers,
            json={"category_id": category_id, "title": "群内分享", "content": "群内帖子内容"},
        )
        assert group_post.status_code == 201, group_post.text
        posts = client.get(f"/api/groups/{group_id}/posts", headers=member_headers)
        assert posts.status_code == 200 and posts.json()["data"]["total"] == 1

        sent = client.post(
            "/api/messages",
            headers=owner_headers,
            json={"receiver_id": member_id, "content": "欢迎加入群组"},
        )
        assert sent.status_code == 201, sent.text
        conversations = client.get("/api/messages", headers=member_headers)
        assert conversations.status_code == 200
        assert conversations.json()["data"]["items"][0]["other_user"]["id"] == owner_id
        messages = client.get(
            "/api/messages", headers=member_headers, params={"other_user_id": owner_id}
        )
        assert messages.status_code == 200
        assert messages.json()["data"]["items"][0]["is_read"] is True


if __name__ == "__main__":
    try:
        run()
        print("community API tests passed")
    finally:
        Path("test_community.db").unlink(missing_ok=True)
