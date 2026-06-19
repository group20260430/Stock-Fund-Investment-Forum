"""Risk assessment record model — stores each questionnaire submission for history."""

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Enum, JSON, Integer, TIMESTAMP, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base


class RiskLevelEnum(str, enum.Enum):
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    answers: Mapped[list] = mapped_column(JSON, nullable=False)
    total_questions: Mapped[int] = mapped_column(Integer, default=15, nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    max_score: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    risk_level: Mapped[RiskLevelEnum] = mapped_column(
        Enum(RiskLevelEnum), nullable=False
    )
    suggestion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"<RiskAssessment(id={self.id}, user_id={self.user_id}, "
            f"risk_level={self.risk_level.value})>"
        )
