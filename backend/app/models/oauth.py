import enum
from datetime import datetime

from sqlalchemy import Enum, ForeignKey, Integer, JSON, String, TIMESTAMP, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base


class OAuthProvider(str, enum.Enum):
    QQ = "qq"
    WECHAT = "wechat"
    WEIBO = "weibo"


class OAuthAccount(Base):
    __tablename__ = "oauth_accounts"
    __table_args__ = (
        UniqueConstraint("provider", "openid", name="uq_oauth_provider_openid"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    provider: Mapped[OAuthProvider] = mapped_column(Enum(OAuthProvider), nullable=False, index=True)
    openid: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    unionid: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    nickname: Mapped[str | None] = mapped_column(String(100), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    raw_profile: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user = relationship("User")
