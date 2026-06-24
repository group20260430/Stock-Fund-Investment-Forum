import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import Integer, Enum, ForeignKey, String, JSON, TIMESTAMP, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ProfessionalCertStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ProfessionalCertification(Base):
    """专业认证申请表 — 上传从业资格/学历证明等材料"""
    __tablename__ = "professional_certifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # JSON 格式：[{"name": "证券从业资格证", "url": "/uploads/xxx.pdf"}, ...]
    qualification_docs: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment="申请说明，如从业经历简述"
    )
    status: Mapped[ProfessionalCertStatus] = mapped_column(
        Enum(ProfessionalCertStatus),
        default=ProfessionalCertStatus.PENDING,
        nullable=False,
        index=True,
    )
    reviewer_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    review_comment: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<ProfessionalCertification(id={self.id}, user_id={self.user_id}, status={self.status.value})>"
