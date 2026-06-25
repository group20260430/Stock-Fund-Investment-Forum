import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import Integer, Boolean, Enum, JSON, String, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base


class UserRole(str, enum.Enum):
    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"


class UserStatus(str, enum.Enum):
    ACTIVE = "active"
    DISABLED = "disabled"


class AuthLevel(str, enum.Enum):
    NONE = "none"
    BASIC = "basic"
    VERIFIED = "verified"
    PROFESSIONAL = "professional"


class RiskLevel(str, enum.Enum):
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


class RegisterType(str, enum.Enum):
    PHONE = "phone"
    EMAIL = "email"
    QQ = "qq"
    WECHAT = "wechat"
    WEIBO = "weibo"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    phone: Mapped[Optional[str]] = mapped_column(String(11), unique=True, nullable=True, index=True)
    email: Mapped[Optional[str]] = mapped_column(String(120), unique=True, nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    nickname: Mapped[str] = mapped_column(String(50), nullable=False)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole), default=UserRole.USER, nullable=False
    )
    auth_level: Mapped[AuthLevel] = mapped_column(
        Enum(AuthLevel), default=AuthLevel.NONE, nullable=False
    )
    risk_level: Mapped[Optional[RiskLevel]] = mapped_column(
        Enum(RiskLevel), nullable=True
    )
    status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus), default=UserStatus.ACTIVE, nullable=False
    )
    register_type: Mapped[RegisterType] = mapped_column(
        Enum(RegisterType), default=RegisterType.PHONE, nullable=False
    )
    investment_tags: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    follow_markets: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    privacy_settings: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    is_professional: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ban_expires_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP, nullable=True)
    banned_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    followers_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    following_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        identifier = self.phone or self.email or f"id={self.id}"
        return f"<User(id={self.id}, identifier={identifier}, nickname={self.nickname})>"
