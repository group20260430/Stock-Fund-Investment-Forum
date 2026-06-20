import enum
from datetime import datetime

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, JSON, String, Text, TIMESTAMP, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base


class PostType(str, enum.Enum):
    NORMAL = "normal"
    LONG_ARTICLE = "long_article"
    POLL = "poll"
    MOMENT = "moment"


class PostStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    REVIEWING = "reviewing"
    REJECTED = "rejected"


class CommentStatus(str, enum.Enum):
    PUBLISHED = "published"
    REVIEWING = "reviewing"
    REJECTED = "rejected"


class LikeTarget(str, enum.Enum):
    POST = "post"
    COMMENT = "comment"


class ShareType(str, enum.Enum):
    TIMELINE = "timeline"
    MESSAGE = "message"
    GROUP = "group"


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    post_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now())


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id", ondelete="RESTRICT"), index=True)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    post_type: Mapped[PostType] = mapped_column(Enum(PostType), default=PostType.NORMAL, nullable=False)
    status: Mapped[PostStatus] = mapped_column(Enum(PostStatus), default=PostStatus.PUBLISHED, nullable=False)
    is_elite: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    tags: Mapped[list | None] = mapped_column(JSON)
    view_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    like_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    comment_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    collect_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    share_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_activity_at: Mapped[datetime | None] = mapped_column(TIMESTAMP)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    author = relationship("User")
    category = relationship("Category")
    attachments = relationship("Attachment", cascade="all, delete-orphan")
    vote_options = relationship("VoteOption", cascade="all, delete-orphan", order_by="VoteOption.sort_order")


class Attachment(Base):
    __tablename__ = "attachments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"), index=True)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_url: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    file_type: Mapped[str] = mapped_column(String(100), default="application/octet-stream", nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now())


class VoteOption(Base):
    __tablename__ = "vote_options"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"), index=True)
    label: Mapped[str] = mapped_column(String(200), nullable=False)
    vote_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now())


class VoteRecord(Base):
    __tablename__ = "vote_records"
    __table_args__ = (UniqueConstraint("user_id", "post_id", "option_id", name="uq_vote_record"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"), index=True)
    option_id: Mapped[int] = mapped_column(ForeignKey("vote_options.id", ondelete="CASCADE"), index=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now(), onupdate=func.now())


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("comments.id", ondelete="CASCADE"), index=True)
    reply_to_id: Mapped[int | None] = mapped_column(ForeignKey("comments.id", ondelete="SET NULL"))
    content: Mapped[str] = mapped_column(Text, nullable=False)
    like_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[CommentStatus] = mapped_column(Enum(CommentStatus), default=CommentStatus.PUBLISHED, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    author = relationship("User", foreign_keys=[user_id])
    reply_to = relationship("Comment", remote_side="Comment.id", foreign_keys=[reply_to_id])


class Like(Base):
    __tablename__ = "likes"
    __table_args__ = (UniqueConstraint("user_id", "target_type", "target_id", name="uq_like_target"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    target_type: Mapped[LikeTarget] = mapped_column(Enum(LikeTarget), nullable=False)
    target_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now())


class FavoriteFolder(Base):
    __tablename__ = "favorite_folders"
    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_favorite_folder_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(50), default="默认收藏夹", nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now())


class Favorite(Base):
    __tablename__ = "favorites"
    __table_args__ = (UniqueConstraint("user_id", "post_id", name="uq_favorite_post"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"), index=True)
    folder_id: Mapped[int] = mapped_column(ForeignKey("favorite_folders.id", ondelete="CASCADE"), index=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now())

    post = relationship("Post")
    folder = relationship("FavoriteFolder")


class Share(Base):
    __tablename__ = "shares"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"), index=True)
    share_type: Mapped[ShareType] = mapped_column(Enum(ShareType), nullable=False)
    comment: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now())
