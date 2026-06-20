from fastapi import APIRouter, Depends, Query, Request
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.dependencies import RateLimiter, get_current_user, security
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import (
    ApiResponse,
    CertificationRequest,
    LoginRequest,
    RegisterRequest,
    RiskAssessmentRequest,
    SendCodeRequest,
    UpdateProfileRequest,
)
from app.services.user_service import UserService

router = APIRouter(tags=["用户系统"])

# Rate limiters: 5 requests per 60 seconds for auth endpoints
register_limiter = RateLimiter(max_requests=5, window_seconds=60)
login_limiter = RateLimiter(max_requests=5, window_seconds=60)
code_limiter = RateLimiter(max_requests=5, window_seconds=60)
refresh_limiter = RateLimiter(max_requests=10, window_seconds=60)


# ==================== 注册与认证 ====================


@router.post("/auth/register", status_code=201)
async def register(
    data: RegisterRequest,
    request: Request,
    db: Session = Depends(get_db),
    _: None = Depends(register_limiter),
):
    """用户注册 — 手机号 + 密码注册，返回用户ID和JWT Token。"""
    result = UserService.register(db, data)
    return ApiResponse(code=201, message="注册成功", data=result)


@router.post("/auth/send-code")
async def send_code(
    data: SendCodeRequest,
    request: Request,
    db: Session = Depends(get_db),
    _: None = Depends(code_limiter),
):
    """发送验证码 — 模拟短信发送，返回验证码有效时长。"""
    result = UserService.send_code(db, data)
    return ApiResponse(code=200, message="验证码已发送", data=result)


@router.post("/auth/login")
async def login(
    data: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
    _: None = Depends(login_limiter),
):
    """用户登录 — 支持密码登录和验证码登录。"""
    result = UserService.login(db, data)
    return ApiResponse(code=200, message="登录成功", data=result)


@router.post("/auth/refresh")
async def refresh_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
    _: None = Depends(refresh_limiter),
):
    """刷新Token — 使用 Refresh Token 换取新的 Access + Refresh Token 对。

    客户端应在请求头中发送当前 Refresh Token（而非 Access Token）。
    旧 Refresh Token 会被立即撤销（token rotation）。
    """
    raw_token = credentials.credentials
    result = UserService.refresh_token(raw_token, db)
    return ApiResponse(code=200, message="Token 已刷新", data=result)


# ==================== 个人资料管理 ====================


@router.get("/auth/me")
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取当前用户信息 — 返回完整个人资料（手机号脱敏）。"""
    result = UserService.get_profile(db, current_user)
    return ApiResponse(code=200, message="success", data=result)


@router.put("/auth/profile")
async def update_profile(
    data: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新个人资料 — 支持部分更新。"""
    UserService.update_profile(db, current_user, data)
    result = UserService.get_profile(db, current_user)
    return ApiResponse(code=200, message="更新成功", data=result)


# ==================== 实名认证 & 风险评估 ====================


@router.post("/auth/certification")
async def submit_certification(
    data: CertificationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """申请实名认证 — 提交身份证信息，等待审核。"""
    result = UserService.submit_certification(db, current_user, data)
    return ApiResponse(code=200, message="认证申请已提交，等待审核", data=result)


@router.post("/auth/risk-assessment")
async def risk_assessment(
    data: RiskAssessmentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """提交风险评估问卷 — 返回风险等级和投资建议，同时持久化记录。"""
    result = UserService.submit_risk_assessment(db, current_user, data)
    return ApiResponse(code=200, message="评估完成", data=result)


@router.get("/auth/risk-assessment/questions")
async def get_risk_questions(
    current_user: User = Depends(get_current_user),
):
    """获取风险评估问卷 — 返回完整的题目列表（含选项和分值）。"""
    questions = UserService.get_risk_questions()
    return ApiResponse(code=200, message="success", data=questions)


@router.get("/auth/risk-assessment/history")
async def get_risk_assessment_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=50, description="每页数量"),
):
    """获取历史评估记录 — 支持分页，按评估时间倒序排列。"""
    result = UserService.get_risk_assessment_history(db, current_user, page, size)
    return ApiResponse(code=200, message="success", data=result)
