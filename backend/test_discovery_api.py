import os
import gc
import time
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite:///./test_discovery.db"
Path("test_discovery.db").unlink(missing_ok=True)

from fastapi.testclient import TestClient

from app.db.session import engine
from app.main import app


def register(client: TestClient, phone: str, nickname: str) -> tuple[int, dict[str, str]]:
    response = client.post(
        "/api/auth/register",
        json={"phone": phone, "password": "Discovery123", "nickname": nickname},
    )
    data = response.json()["data"]
    return data["user_id"], {"Authorization": f"Bearer {data['token']}"}


def run() -> None:
    with TestClient(app) as client:
        reader_id, reader_headers = register(client, "13800005001", "Reader")
        author_id, author_headers = register(client, "13800005002", "Analyst")
        category_id = client.get("/api/categories").json()["data"][0]["id"]
        client.post(f"/api/users/{author_id}/follow", headers=reader_headers)
        created = client.post(
            "/api/posts",
            headers=author_headers,
            json={
                "category_id": category_id,
                "title": "沪深300定投分析",
                "content": "宽基指数长期定投策略",
                "tags": ["沪深300", "定投"],
            },
        )
        assert created.status_code == 201

        feed = client.get("/api/feed", headers=reader_headers)
        assert feed.status_code == 200 and feed.json()["data"]["total"] == 1
        assert feed.json()["data"]["items"][0]["author"]["id"] == author_id

        hot = client.get("/api/hot", params={"period": "daily"})
        assert hot.status_code == 200
        assert hot.json()["data"][0]["topic"] in ("沪深300", "定投")

        posts = client.get("/api/search", params={"keyword": "定投", "type": "post"})
        assert posts.status_code == 200 and posts.json()["data"]["total"] == 1
        users = client.get("/api/search", params={"keyword": "Analyst", "type": "user"})
        assert users.json()["data"]["items"][0]["id"] == author_id
        stocks = client.get("/api/search", params={"keyword": "000300", "type": "stock"})
        assert stocks.json()["data"]["items"][0]["name"] == "沪深300"

        suggestions = client.get("/api/search/suggestions", params={"keyword": "沪深"})
        assert suggestions.status_code == 200
        assert suggestions.json()["data"]["stocks"][0]["code"] == "000300"
        assert "沪深300" in suggestions.json()["data"]["topics"]


if __name__ == "__main__":
    try:
        run()
        print("discovery API tests passed")
    finally:
        engine.dispose()
        gc.collect()
        for attempt in range(3):
            try:
                Path("test_discovery.db").unlink(missing_ok=True)
                break
            except PermissionError:
                if attempt == 2:
                    print("WARNING | cleanup failed for test_discovery.db")
                    break
                time.sleep(0.2)
                gc.collect()
