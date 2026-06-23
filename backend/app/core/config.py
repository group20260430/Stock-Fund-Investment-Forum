from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# ── 项目根目录（backend/），用于解析相对路径 ──
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    project_name: str = "Stock Fund Investment Forum"
    version: str = "0.1.0"
    allowed_origins: list[str] = ["http://localhost:5173"]
    allowed_origin_regex: str = r"http://(localhost|127\.0\.0\.1):\d+"

    # --- Database ---
    # Set DATABASE_URL in .env to override.  Defaults to SQLite for local dev.
    # MySQL example: mysql+pymysql://user:pass@127.0.0.1:3306/stock_fund_forum?charset=utf8mb4
    database_url: str = "sqlite:///./stock_fund_forum.db"

    # --- MySQL (used only when DATABASE_URL is not explicitly set) ---
    mysql_host: str = "127.0.0.1"
    mysql_port: int = 3306
    mysql_user: str = "forum_user"
    mysql_password: str = "forum_password"
    mysql_database: str = "stock_fund_forum"

    # --- JWT ---
    # Access Token: 2 hours  (architect.md §8.1)
    # Refresh Token: 7 days   (architect.md §8.1, db.md §3.1.5)
    jwt_secret: str = "your-jwt-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_hours: int = 2
    refresh_token_expire_days: int = 7

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    def model_post_init(self, __context) -> None:
        """将 SQLite 相对路径解析为基于项目根目录的绝对路径，避免 CWD 问题。"""
        if self.database_url.startswith("sqlite:///./"):
            rel = self.database_url.removeprefix("sqlite:///./")
            self.database_url = f"sqlite:///{_PROJECT_ROOT / rel}"

    @property
    def access_token_expire_seconds(self) -> int:
        return self.access_token_expire_hours * 3600

    @property
    def refresh_token_expire_seconds(self) -> int:
        return self.refresh_token_expire_days * 86400


settings = Settings()
