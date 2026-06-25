from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.dependencies import RateLimiter, get_current_user, security
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User
from app.models.points import PointsHistory
from app.schemas.privacy import PrivacySettingsSchema
from app.schemas.user import (
    ApiResponse,
    CertificationRequest,
    EmailRegisterRequest,
    EmailSendCodeRequest,
    LoginRequest,
    ProfessionalCertificationRequest,
    RegisterRequest,
    ResetPasswordRequest,
    RiskAssessmentRequest,
    SendCodeRequest,
    UpdateProfileRequest,
    VerifyCodeRequest,
)
from app.services.user_service import UserService
from app.services.qq_oauth_service import QQOAuthService

router = APIRouter(tags=["用户系统"])

# Rate limiters: 5 requests per 60 seconds for auth endpoints
register_limiter = RateLimiter(max_requests=5, window_seconds=60)
login_limiter = RateLimiter(max_requests=5, window_seconds=60)
code_limiter = RateLimiter(max_requests=5, window_seconds=60)
email_code_limiter = RateLimiter(max_requests=5, window_seconds=60)
email_register_limiter = RateLimiter(max_requests=5, window_seconds=60)
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


@router.post("/auth/email/send-code")
async def email_send_code(
    data: EmailSendCodeRequest,
    request: Request,
    db: Session = Depends(get_db),
    _: None = Depends(email_code_limiter),
):
    """发送邮箱验证码 — 用于邮箱注册/登录验证。"""
    result = await UserService.send_email_code(db, data)
    return ApiResponse(code=200, message="验证码已发送", data=result)


@router.post("/auth/verify-code")
async def verify_code(
    data: VerifyCodeRequest,
    request: Request,
    _: None = Depends(code_limiter),
):
    """验证手机验证码 — 验证通过后方可注册/重置密码。"""
    result = UserService.verify_code(data.phone, data.code, data.type)
    return ApiResponse(code=200, message="验证成功", data=result)


@router.post("/auth/reset-password")
async def reset_password(
    data: ResetPasswordRequest,
    request: Request,
    db: Session = Depends(get_db),
    _: None = Depends(code_limiter),
):
    """重置密码 — 验证码验证通过后，设置新密码。"""
    result = UserService.reset_password(db, data)
    return ApiResponse(code=200, message="密码重置成功", data=result)


@router.post("/auth/email/verify-code")
async def email_verify_code(
    data: dict,
    request: Request,
    _: None = Depends(email_code_limiter),
):
    """验证邮箱验证码 — 验证通过后方可注册。"""
    email = (data.get("email") or "").strip()
    code = (data.get("code") or "").strip()
    if not email or not code:
        raise HTTPException(status_code=400, detail="邮箱和验证码不能为空")
    result = UserService.verify_email_code(email, code)
    return ApiResponse(code=200, message="验证成功", data=result)


@router.post("/auth/email/register", status_code=201)
async def email_register(
    data: EmailRegisterRequest,
    request: Request,
    db: Session = Depends(get_db),
    _: None = Depends(email_register_limiter),
):
    """邮箱注册 — 先发送验证码并验证，再调用此接口完成注册。"""
    result = UserService.register_by_email(db, data)
    return ApiResponse(code=201, message="注册成功", data=result)


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


@router.get("/auth/qq/login")
async def qq_login(redirect: str | None = Query("/", description="登录成功后的前端跳转路径")):
    """QQ 登录入口 — 返回 QQ 授权页跳转。"""
    return RedirectResponse(QQOAuthService.build_authorize_url(redirect))


@router.get("/auth/qq/callback")
async def qq_callback(
    code: str | None = Query(None),
    state: str | None = Query(None),
    error: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """QQ OAuth 回调 — 换取 QQ 用户信息并签发本系统 Token。"""
    if error:
        raise HTTPException(status_code=400, detail=f"QQ 登录失败: {error}")
    if not code:
        raise HTTPException(status_code=400, detail="QQ 登录缺少 code")
    result = await QQOAuthService.handle_callback(db, code, state)
    return RedirectResponse(QQOAuthService.build_frontend_redirect(result))


@router.post("/auth/reset-password")
async def reset_password(
    data: ResetPasswordRequest,
    request: Request,
    db: Session = Depends(get_db),
    _: None = Depends(code_limiter),
):
    """忘记密码 — 使用手机号/邮箱验证码重置密码。"""
    result = UserService.reset_password(db, data)
    return ApiResponse(code=200, message="密码已重置", data=result)


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


# ==================== 隐私设置 ====================


@router.get("/auth/privacy")
async def get_privacy_settings(
    current_user: User = Depends(get_current_user),
):
    """获取当前用户的隐私设置 — 返回合并默认值后的完整设置。"""
    defaults = PrivacySettingsSchema().model_dump()
    stored = current_user.privacy_settings or {}
    merged = {**defaults, **stored}
    return ApiResponse(code=200, message="success", data=merged)


@router.put("/auth/privacy")
async def update_privacy_settings(
    data: PrivacySettingsSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新隐私设置 — 支持部分更新，未传字段保持原值。"""
    stored = current_user.privacy_settings or {}
    # Only update fields that differ from defaults (partial update)
    update_data = data.model_dump(exclude_unset=True)
    stored.update(update_data)
    current_user.privacy_settings = stored
    db.commit()
    # Return merged with defaults
    defaults = PrivacySettingsSchema().model_dump()
    merged = {**defaults, **stored}
    return ApiResponse(code=200, message="隐私设置已更新", data=merged)


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


@router.post("/auth/professional-certification")
async def submit_professional_certification(
    data: ProfessionalCertificationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """申请专业认证 — 上传从业资格、学历证明等材料，审核通过后获得加V标识。"""
    result = UserService.submit_professional_certification(db, current_user, data)
    return ApiResponse(code=200, message="专业认证申请已提交，等待审核", data=result)


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


# ==================== 积分与等级 ====================


@router.get("/auth/points/history")
async def get_points_history(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=50, description="每页数量"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取当前用户的积分变动记录 — 支持分页，按时间倒序排列。"""
    query = db.query(PointsHistory).filter(PointsHistory.user_id == current_user.id)
    total = query.count()
    items = (
        query.order_by(PointsHistory.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )
    return ApiResponse(code=200, message="success", data={
        "items": [
            {
                "id": item.id,
                "points_change": item.points_change,
                "reason": item.reason,
                "reference_type": item.reference_type,
                "reference_id": item.reference_id,
                "created_at": item.created_at,
            }
            for item in items
        ],
        "total": total,
        "page": page,
        "size": size,
    })
