import enum
from datetime import date, datetime

from sqlalchemy import Boolean, Date, Enum, ForeignKey, Integer, String, TIMESTAMP, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base


class ReportTarget(str, enum.Enum):
    POST = "post"
    COMMENT = "comment"
    USER = "user"


class ReportReason(str, enum.Enum):
    FAKE_INFO = "fake_info"
    PERSONAL_ATTACK = "personal_attack"
    ILLEGAL_STOCK_PROMOTION = "illegal_stock_promotion"
    SPAM = "spam"
    OTHER = "other"


class ReportStatus(str, enum.Enum):
    PENDING = "pending"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class ReviewTarget(str, enum.Enum):
    POST = "post"
    COMMENT = "comment"


class ReviewAction(str, enum.Enum):
    APPROVE = "approve"
    REJECT = "reject"
    EDIT = "edit"


class BanAction(str, enum.Enum):
    BAN = "ban"
    UNBAN = "unban"


class SensitiveLevel(str, enum.Enum):
    BLOCK = "block"
    REVIEW = "review"
    WARN = "warn"


class ActivityType(str, enum.Enum):
    LOGIN = "login"
    POST = "post"
    COMMENT = "comment"
    LIKE = "like"
    FOLLOW = "follow"
    UNFOLLOW = "unfollow"
    SHARE = "share"
    VOTE = "vote"


class Report(Base):
    __tablename__ = "reports"
    __table_args__ = (UniqueConstraint("reporter_id", "target_type", "target_id", name="uq_report_target"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    reporter_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    target_type: Mapped[ReportTarget] = mapped_column(Enum(ReportTarget), nullable=False)
    target_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    reason: Mapped[ReportReason] = mapped_column(Enum(ReportReason), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[ReportStatus] = mapped_column(Enum(ReportStatus), default=ReportStatus.PENDING)
    handler_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    handle_comment: Mapped[str | None] = mapped_column(String(500))
    handled_at: Mapped[datetime | None] = mapped_column(TIMESTAMP)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now())


class ReviewLog(Base):
    __tablename__ = "review_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    target_type: Mapped[ReviewTarget] = mapped_column(Enum(ReviewTarget), nullable=False)
    target_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    reviewer_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    action: Mapped[ReviewAction] = mapped_column(Enum(ReviewAction), nullable=False)
    comment: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now())


class BanRecord(Base):
    __tablename__ = "ban_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    admin_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    action: Mapped[BanAction] = mapped_column(Enum(BanAction), nullable=False)
    reason: Mapped[str | None] = mapped_column(String(500))
    duration_hours: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now())


class SensitiveWord(Base):
    __tablename__ = "sensitive_words"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    word: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    level: Mapped[SensitiveLevel] = mapped_column(Enum(SensitiveLevel), default=SensitiveLevel.REVIEW)
    category: Mapped[str | None] = mapped_column(String(50))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now())


class DailyStat(Base):
    __tablename__ = "daily_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    stat_date: Mapped[date] = mapped_column(Date, unique=True, nullable=False)
    dau: Mapped[int] = mapped_column(Integer, default=0)
    new_users: Mapped[int] = mapped_column(Integer, default=0)
    total_posts: Mapped[int] = mapped_column(Integer, default=0)
    total_comments: Mapped[int] = mapped_column(Integer, default=0)
    total_likes: Mapped[int] = mapped_column(Integer, default=0)
    total_shares: Mapped[int] = mapped_column(Integer, default=0)
    reports_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now(), onupdate=func.now())


class UserActivityLog(Base):
    __tablename__ = "user_activity_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    activity_type: Mapped[ActivityType] = mapped_column(Enum(ActivityType), nullable=False, index=True)
    target_type: Mapped[str | None] = mapped_column(String(20))
    target_id: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now(), index=True)
