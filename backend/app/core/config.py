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
    # 默认使用 backend/ 目录下的 SQLite 文件（通过 _PROJECT_ROOT 解析为绝对路径）
    # MySQL example: mysql+pymysql://user:pass@127.0.0.1:3306/stock_fund_forum?charset=utf8mb4
    database_url: str = f"sqlite:///{_PROJECT_ROOT / 'stock_fund_forum.db'}"

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

    # --- SMTP ---
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""
    smtp_timeout: int = 10

    # --- QQ OAuth ---
    qq_oauth_app_id: str = ""
    qq_oauth_app_key: str = ""
    qq_oauth_redirect_uri: str = "http://localhost:8000/api/auth/qq/callback"
    frontend_base_url: str = "http://localhost:5173"

    # --- Admin seed ---
    admin_phone: str = "13800000000"
    admin_email: str = "admin@forum.local"
    admin_password: str = "Admin@123456"
    admin_nickname: str = "系统管理员"

    model_config = SettingsConfigDict(
        env_file=str(_PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def access_token_expire_seconds(self) -> int:
        return self.access_token_expire_hours * 3600

    @property
    def refresh_token_expire_seconds(self) -> int:
        return self.refresh_token_expire_days * 86400

    @property
    def smtp_use_ssl(self) -> bool:
        """Auto-detect SSL mode by port: 465 → SSL, others → STARTTLS."""
        return self.smtp_port == 465

    @property
    def smtp_configured(self) -> bool:
        return bool(
            self.smtp_host
            and self.smtp_user
            and self.smtp_password
            and self.smtp_from_email
        )


settings = Settings()
