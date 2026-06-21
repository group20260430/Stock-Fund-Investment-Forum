import os
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite:///./test_social.db"
Path("test_social.db").unlink(missing_ok=True)

from fastapi.testclient import TestClient

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

        followed = client.post(f"/api/users/{bob_id}/follow", headers=alice_headers)
        assert followed.status_code == 200, followed.text
        assert followed.json()["data"] == {"is_followed": True, "followers_count": 1}

        profile = client.get(f"/api/users/{bob_id}", headers=alice_headers)
        assert profile.status_code == 200
        assert profile.json()["data"]["is_followed"] is True
        assert "phone" not in profile.json()["data"]

        followers = client.get(f"/api/users/{bob_id}/followers", headers=bob_headers)
        assert followers.json()["data"]["items"][0]["id"] == alice_id
        following = client.get(f"/api/users/{alice_id}/following", headers=alice_headers)
        assert following.json()["data"]["items"][0]["id"] == bob_id

        starred = client.put(
            "/api/users/me/starred",
            headers=alice_headers,
            json={"user_id": bob_id, "is_starred": True},
        )
        assert starred.status_code == 200 and starred.json()["data"]["is_starred"] is True
        assert client.get(f"/api/users/{bob_id}", headers=alice_headers).json()["data"]["is_starred"] is True

        unfollowed = client.post(f"/api/users/{bob_id}/follow", headers=alice_headers)
        assert unfollowed.json()["data"] == {"is_followed": False, "followers_count": 0}
        assert client.post(f"/api/users/{alice_id}/follow", headers=alice_headers).status_code == 400


if __name__ == "__main__":
    try:
        run()
        print("social API tests passed")
    finally:
        Path("test_social.db").unlink(missing_ok=True)
