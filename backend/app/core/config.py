from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    project_name: str = "Stock Fund Investment Forum"
    version: str = "0.1.0"
    allowed_origins: list[str] = ["http://localhost:5173"]

    mysql_host: str = "127.0.0.1"
    mysql_port: int = 3306
    mysql_user: str = "forum_user"
    mysql_password: str = "forum_password"
    mysql_database: str = "stock_fund_forum"

    jwt_secret: str = "your-jwt-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 24

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

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
        return self.jwt_expire_hours * 3600


settings = Settings()
