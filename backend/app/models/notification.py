import enum
from datetime import datetime

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, String, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base


class NotificationType(str, enum.Enum):
    FOLLOW = "follow"
    GROUP_INVITE = "group_invite"
    GROUP_JOIN_REQUEST = "group_join_request"
    GROUP_APPROVED = "group_approved"
    GROUP_REJECTED = "group_rejected"
    NEW_MESSAGE = "new_message"
    SYSTEM = "system"


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    type: Mapped[NotificationType] = mapped_column(
        Enum(NotificationType), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(String(500), nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    target_type: Mapped[str | None] = mapped_column(String(20))
    target_id: Mapped[int | None] = mapped_column(Integer)
    sender_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now())

    user = relationship("User", foreign_keys=[user_id], backref="notifications")
    sender = relationship("User", foreign_keys=[sender_id])
