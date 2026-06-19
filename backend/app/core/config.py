from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    project_name: str = "Stock Fund Investment Forum"
    version: str = "0.1.0"
    allowed_origins: list[str] = ["http://localhost:5173"]

    # --- MySQL ---
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

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # --- Derived values ---
    @property
    def database_url(self) -> str:
        return (
            "mysql+pymysql://"
            f"{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
            "?charset=utf8mb4"
        )

    @property
    def access_token_expire_seconds(self) -> int:
        return self.access_token_expire_hours * 3600

    @property
    def refresh_token_expire_seconds(self) -> int:
        return self.refresh_token_expire_days * 86400


settings = Settings()
