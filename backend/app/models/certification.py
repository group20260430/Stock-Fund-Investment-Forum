"""Real-name certification record model.

PII fields (real_name, id_number) should be AES-256 encrypted at the application layer
before storage.  Keys are injected via environment variables.
"""

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Enum, String, TIMESTAMP, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base


class CertificationStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class Certification(Base):
    __tablename__ = "certifications"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    real_name: Mapped[str] = mapped_column(String(255), nullable=False)
    id_number: Mapped[str] = mapped_column(String(255), nullable=False)
    id_card_front: Mapped[str] = mapped_column(String(500), nullable=False)
    id_card_back: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[CertificationStatus] = mapped_column(
        Enum(CertificationStatus), default=CertificationStatus.PENDING, nullable=False
    )
    reviewer_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    review_comment: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"<Certification(id={self.id}, user_id={self.user_id}, "
            f"status={self.status.value})>"
        )
