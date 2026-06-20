import os
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite:///./test_interactions.db"
Path("test_interactions.db").unlink(missing_ok=True)

from fastapi.testclient import TestClient

from app.main import app


def run() -> None:
    with TestClient(app) as client:
        registered = client.post(
            "/api/auth/register",
            json={"phone": "13800002001", "password": "Interact123", "nickname": "interactor"},
        )
        token = registered.json()["data"]["token"]
        headers = {"Authorization": f"Bearer {token}"}
        category_id = client.get("/api/categories").json()["data"][0]["id"]
        created = client.post(
            "/api/posts",
            headers=headers,
            json={"category_id": category_id, "title": "互动测试", "content": "测试评论、点赞、收藏和分享"},
        )
        post_id = created.json()["data"]["id"]

        liked = client.post(f"/api/posts/{post_id}/like", headers=headers)
        assert liked.status_code == 200 and liked.json()["data"]["is_liked"] is True

        collected = client.post(
            f"/api/posts/{post_id}/collect", headers=headers, json={"folder_name": "研究"}
        )
        assert collected.status_code == 200 and collected.json()["data"]["is_collected"] is True
        detail = client.get(f"/api/posts/{post_id}", headers=headers).json()["data"]
        assert detail["is_liked"] is True and detail["is_collected"] is True

        root = client.post(
            f"/api/posts/{post_id}/comments", headers=headers, json={"content": "一级评论"}
        )
        assert root.status_code == 201, root.text
        root_id = root.json()["data"]["id"]
        reply = client.post(
            f"/api/posts/{post_id}/comments",
            headers=headers,
            json={"content": "回复内容", "parent_id": root_id, "reply_to_id": root_id},
        )
        assert reply.status_code == 201, reply.text
        comment_like = client.post(f"/api/comments/{root_id}/like", headers=headers)
        assert comment_like.status_code == 200 and comment_like.json()["data"]["like_count"] == 1

        comments = client.get(f"/api/posts/{post_id}/comments", headers=headers)
        assert comments.status_code == 200, comments.text
        assert comments.json()["data"]["total"] == 1
        assert len(comments.json()["data"]["items"][0]["replies"]) == 1
        assert comments.json()["data"]["items"][0]["is_liked"] is True

        shared = client.post(
            f"/api/posts/{post_id}/share",
            headers=headers,
            json={"share_type": "timeline", "comment": "值得一看"},
        )
        assert shared.status_code == 201 and shared.json()["data"]["share_count"] == 1

        collections = client.get("/api/users/me/collections", headers=headers)
        assert collections.status_code == 200
        assert collections.json()["data"]["items"][0]["folder_name"] == "研究"

        unliked = client.post(f"/api/posts/{post_id}/like", headers=headers)
        assert unliked.json()["data"]["is_liked"] is False
        uncollected = client.post(f"/api/posts/{post_id}/collect", headers=headers, json={})
        assert uncollected.json()["data"]["is_collected"] is False


if __name__ == "__main__":
    try:
        run()
        print("interaction API tests passed")
    finally:
        Path("test_interactions.db").unlink(missing_ok=True)
