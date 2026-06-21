from typing import Literal

from pydantic import BaseModel, Field, model_validator


class ReportCreate(BaseModel):
    target_id: int
    target_type: Literal["post", "comment", "user"]
    reason: Literal["fake_info", "personal_attack", "illegal_stock_promotion", "spam", "other"]
    description: str | None = Field(None, max_length=500)


class ReviewRequest(BaseModel):
    action: Literal["approve", "reject", "edit"]
    comment: str | None = Field(None, max_length=500)

    @model_validator(mode="after")
    def reject_requires_comment(self):
        if self.action == "reject" and not self.comment:
            raise ValueError("拒绝时必须填写审核意见")
        return self


class BanRequest(BaseModel):
    action: Literal["ban", "unban"]
    reason: str | None = Field(None, max_length=500)
    duration_hours: int | None = Field(None, ge=1, le=24 * 365)


class CategoryRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    description: str | None = Field(None, max_length=255)
    sort_order: int = 0
    is_active: bool = True


class ReportHandleRequest(BaseModel):
    action: Literal["resolve", "dismiss"]
    comment: str | None = Field(None, max_length=500)


class SensitiveWordRequest(BaseModel):
    word: str = Field(..., min_length=1, max_length=100)
    level: Literal["block", "review", "warn"] = "review"
    category: str | None = Field(None, max_length=50)
    is_active: bool = True


class CertificationReviewRequest(BaseModel):
    action: Literal["approve", "reject"]
    comment: str | None = Field(None, max_length=500)
