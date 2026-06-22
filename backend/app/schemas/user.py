import re
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


# ==================== Request Schemas ====================


class RegisterRequest(BaseModel):
    phone: str = Field(..., pattern=r"^\d{11}$", description="手机号，11位数字")
    password: str = Field(
        ..., min_length=8, max_length=32, description="密码，8~32位，含字母+数字"
    )
    nickname: Optional[str] = Field(None, min_length=2, max_length=20)
    avatar_url: Optional[str] = None
    register_type: Optional[str] = Field(
        "phone", pattern=r"^(phone|email|wechat|weibo)$"
    )

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if not re.search(r"[A-Za-z]", v):
            raise ValueError("密码必须包含字母")
        if not re.search(r"\d", v):
            raise ValueError("密码必须包含数字")
        return v


class SendCodeRequest(BaseModel):
    phone: str = Field(..., pattern=r"^\d{11}$")
    type: str = Field(..., pattern=r"^(register|login|reset_password)$")


class LoginRequest(BaseModel):
    phone: str = Field(..., min_length=1, description="手机号或邮箱")
    password: Optional[str] = Field(None, description="密码（密码登录时必填）")
    code: Optional[str] = Field(None, description="验证码（验证码登录时必填）")
    login_type: str = Field(..., pattern=r"^(password|code)$")


class UpdateProfileRequest(BaseModel):
    nickname: Optional[str] = Field(None, min_length=2, max_length=20)
    bio: Optional[str] = Field(None, max_length=500)
    avatar_url: Optional[str] = None
    investment_tags: Optional[list[str]] = None
    follow_markets: Optional[list[str]] = None
    risk_preference: Optional[str] = Field(
        None, pattern=r"^(conservative|moderate|aggressive)$"
    )


class CertificationRequest(BaseModel):
    id_card_front: str = Field(..., min_length=1, description="身份证正面照片(base64)")
    id_card_back: str = Field(..., min_length=1, description="身份证反面照片(base64)")
    real_name: str = Field(..., min_length=1, max_length=50, description="真实姓名")
    id_number: str = Field(
        ...,
        pattern=r"^\d{17}[\dXx]$",
        description="18位身份证号",
    )


class QuestionAnswer(BaseModel):
    question_id: int
    answer: str


class Choice(BaseModel):
    """A single multiple-choice option for a risk assessment question."""

    label: str = Field(..., description="选项标签，如A/B/C/D/E")
    text: str = Field(..., description="选项文本内容")
    score: int = Field(..., ge=1, le=5, description="选项分值")


class RiskQuestion(BaseModel):
    """A single question in the risk assessment questionnaire."""

    question_id: int = Field(..., ge=1, description="题目编号")
    question_text: str = Field(..., description="题目内容")
    choices: list[Choice] = Field(..., min_length=2, description="选项列表")


class RiskAssessmentRequest(BaseModel):
    answers: list[QuestionAnswer] = Field(..., min_length=1)
    total_questions: Optional[int] = Field(
        None, ge=1, description="题目总数，不传则由后端从answers长度推导"
    )


class RiskAssessmentResponse(BaseModel):
    """Response schema for a completed risk assessment."""

    assessment_id: int = Field(..., description="评估记录ID")
    risk_level: str = Field(..., description="风险等级")
    score: int = Field(..., description="得分（0-100）")
    max_score: int = Field(default=100, description="满分")
    suggestion: str = Field(..., description="投资建议")


class RiskHistoryItem(BaseModel):
    """A single historical risk assessment record."""

    id: int
    score: int
    risk_level: str
    total_questions: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ==================== Response Schemas ====================


class Achievements(BaseModel):
    posts_count: int = 0
    elite_posts: int = 0
    influence_score: int = 0
    badges: list[str] = Field(default_factory=list)


class UserProfile(BaseModel):
    id: int
    nickname: str
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    phone: str
    email: Optional[str] = None
    role: str
    auth_level: str
    is_professional: bool = False
    risk_level: Optional[str] = None
    investment_tags: Optional[list[str]] = None
    follow_markets: Optional[list[str]] = None
    achievements: Optional[Achievements] = None
    points: int = 0
    level: int = 1
    privacy_settings: Optional[dict] = None
    created_at: Optional[datetime] = None

    @field_validator("phone", mode="before")
    @classmethod
    def mask_phone(cls, v: str) -> str:
        if v and len(v) == 11:
            return v[:3] + "****" + v[-4:]
        return v

    model_config = {"from_attributes": True}


class ApiResponse(BaseModel):
    code: int
    message: str
    data: Any = None


class PaginatedData(BaseModel):
    items: list[Any]
    total: int
    page: int
    size: int


class PaginatedResponse(BaseModel):
    code: int
    message: str
    data: PaginatedData
