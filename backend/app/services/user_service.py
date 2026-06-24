"""User system business logic — registration, login, refresh tokens, profiles."""

import random
import time
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    create_refresh_token_record,
    decode_access_token,
    get_password_hash,
    hash_refresh_token,
    verify_password,
)
from app.models.certification import Certification, CertificationStatus
from app.models.professional_certification import ProfessionalCertification, ProfessionalCertStatus
from app.models.refresh_token import RefreshToken
from app.models.risk_assessment import RiskAssessment, RiskLevelEnum
from app.models.user import AuthLevel, RegisterType, RiskLevel, User, UserStatus
from app.config import RISK_QUESTIONS
from app.models.operations import ActivityType
from app.models.points import PointsHistory
from app.services.activity_service import record_activity
from app.services.points_service import award_points
from app.schemas.user import (
    Achievements,
    CertificationRequest,
    EmailRegisterRequest,
    EmailSendCodeRequest,
    LoginRequest,
    PaginatedData,
    ProfessionalCertificationRequest,
    RegisterRequest,
    RiskAssessmentRequest,
    RiskHistoryItem,
    SendCodeRequest,
    UpdateProfileRequest,
    UserProfile,
)
from app.services.email_service import EmailSendError, EmailService
from app.core.config import settings


class VerificationCodeStore:
    """In-memory verification code store with TTL cleanup."""

    _codes: dict[str, dict] = {}

    @classmethod
    def set(cls, key: str, code: str, ttl_seconds: int = 300) -> None:
        cls._codes[key] = {"code": code, "expires_at": time.time() + ttl_seconds}

    @classmethod
    def get(cls, key: str) -> str | None:
        entry = cls._codes.get(key)
        if entry is None:
            return None
        if time.time() > entry["expires_at"]:
            del cls._codes[key]
            return None
        return entry["code"]

    @classmethod
    def delete(cls, key: str) -> None:
        cls._codes.pop(key, None)

    @classmethod
    def cleanup_expired(cls) -> int:
        now = time.time()
        expired_keys = [k for k, v in cls._codes.items() if now > v["expires_at"]]
        for k in expired_keys:
            del cls._codes[k]
        return len(expired_keys)


class UserService:
    """User system business logic."""

    # ==================================================================
    # Registration & Verification
    # ==================================================================

    @staticmethod
    def register(db: Session, data: RegisterRequest) -> dict:
        # Check duplicate phone
        existing = db.query(User).filter(User.phone == data.phone).first()
        if existing:
            raise HTTPException(status_code=409, detail="该手机号已注册")

        # Hash password
        password_hash = get_password_hash(data.password)

        # Auto-generate nickname if not provided
        nickname = data.nickname or f"用户{data.phone[-4:] if data.phone else str(random.randint(1000, 9999))}"

        # Map register_type string to enum
        rt = data.register_type or "phone"
        try:
            register_type = RegisterType(rt)
        except ValueError:
            register_type = RegisterType.PHONE

        # Phone registration → auth_level = BASIC (phone-verified)
        auth_level = AuthLevel.BASIC

        # Create user
        user = User(
            phone=data.phone,
            password_hash=password_hash,
            nickname=nickname,
            avatar_url=data.avatar_url,
            register_type=register_type,
            auth_level=auth_level,
            role="user",
            status=UserStatus.ACTIVE,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Issue tokens
        access_token, refresh_token = UserService._issue_token_pair(db, user)

        # Build profile so frontend can cache user info immediately
        profile = UserService._build_profile(user, db)

        return {
            "user_id": user.id,
            "token": access_token,
            "refresh_token": refresh_token,
            "expires_in": 7200,  # 2 hours (access token)
            "user": profile,
        }

    @staticmethod
    def send_code(db: Session, data: SendCodeRequest) -> dict:
        user = db.query(User).filter(User.phone == data.phone).first()

        if data.type == "register":
            if user is not None:
                raise HTTPException(status_code=409, detail="该手机号已注册")
        elif data.type in ("login", "reset_password"):
            if user is None:
                raise HTTPException(status_code=404, detail="该手机号未注册")

        # Generate 6-digit code
        code = str(random.randint(100000, 999999))
        key = f"{data.type}:{data.phone}"
        VerificationCodeStore.set(key, code, ttl_seconds=300)

        # Simulated SMS (safe — no actual PII leaked)
        print(
            f"[SIMULATED SMS] Code for ****{data.phone[-4:]} "
            f"({data.type}): {code}"
        )

        result = {"expire_in": 300}
        # 开发模式：将验证码返回给前端，方便页面 Toast 展示
        if not settings.smtp_configured:
            result["dev_code"] = code
        return result

    @staticmethod
    def verify_code(phone: str, code: str, code_type: str) -> dict:
        """验证手机验证码 — 验证通过后标记已验证。"""
        key = f"{code_type}:{phone}"
        stored_code = VerificationCodeStore.get(key)
        if stored_code is None or stored_code != code:
            raise HTTPException(status_code=401, detail="验证码错误或已过期")

        VerificationCodeStore.delete(key)
        # Mark as verified for subsequent operations (10 min TTL)
        VerificationCodeStore.set(f"verified:{code_type}:{phone}", "1", ttl_seconds=600)

        return {"verified": True}

    @staticmethod
    def reset_password(db: Session, data) -> dict:
        """重置密码 — 验证码验证通过后更新密码。"""
        from app.schemas.user import ResetPasswordRequest

        phone = data.phone
        code = data.code
        new_password = data.password

        # Check that code was verified
        if not VerificationCodeStore.get(f"verified:reset_password:{phone}"):
            raise HTTPException(status_code=400, detail="请先验证验证码")

        # Find user
        user = db.query(User).filter(User.phone == phone).first()
        if user is None:
            raise HTTPException(status_code=404, detail="该手机号未注册")

        # Update password
        user.password_hash = get_password_hash(new_password)
        db.commit()

        # Clean up verification markers
        VerificationCodeStore.delete(f"verified:reset_password:{phone}")

        return {"success": True}

    # ==================================================================
    # Email Verification
    # ==================================================================

    @staticmethod
    async def send_email_code(db: Session, data: EmailSendCodeRequest) -> dict:
        email = data.email.lower().strip()
        user = db.query(User).filter(User.email == email).first()

        if data.type == "register":
            if user is not None:
                raise HTTPException(status_code=409, detail="该邮箱已注册")
        elif data.type in ("login", "reset_password"):
            if user is None:
                raise HTTPException(status_code=404, detail="该邮箱未注册")

        # Generate 6-digit code
        code = str(random.randint(100000, 999999))
        key = f"email:{data.type}:{email}"
        VerificationCodeStore.set(key, code, ttl_seconds=300)

        # Send via email (async)
        try:
            await EmailService.send_verification_code(email, code)
        except EmailSendError as exc:
            # Clean up stored code — user never received it
            VerificationCodeStore.delete(key)
            raise HTTPException(status_code=502, detail=str(exc))

        result = {"expire_in": 300}
        # 开发模式：SMTP 未配置时，将验证码返回给前端
        if not settings.smtp_configured:
            result["dev_code"] = code
        return result

    @staticmethod
    def verify_email_code(email: str, code: str) -> dict:
        email = email.lower().strip()
        key = f"email:register:{email}"
        stored_code = VerificationCodeStore.get(key)
        if stored_code is None or stored_code != code:
            raise HTTPException(status_code=401, detail="验证码错误或已过期")

        VerificationCodeStore.delete(key)
        # Mark as verified for subsequent register call (10 min TTL)
        VerificationCodeStore.set(f"email:verified:{email}", "1", ttl_seconds=600)

        return {"verified": True}

    @staticmethod
    def register_by_email(db: Session, data: EmailRegisterRequest) -> dict:
        email = data.email.lower().strip()

        # Check that email was verified
        if not VerificationCodeStore.get(f"email:verified:{email}"):
            raise HTTPException(status_code=400, detail="请先验证邮箱")

        # Check duplicate email
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            raise HTTPException(status_code=409, detail="该邮箱已注册")

        # Hash password
        password_hash = get_password_hash(data.password)

        # Auto-generate nickname from email local part
        nickname = data.nickname
        if not nickname:
            local_part = email.split("@")[0][:8]
            if len(local_part) < 2:
                local_part += str(random.randint(1000, 9999))
            nickname = f"用户{local_part}"

        # Create user — phone is NULL for email registrations
        user = User(
            phone=None,
            email=email,
            password_hash=password_hash,
            nickname=nickname,
            avatar_url=data.avatar_url,
            register_type=RegisterType.EMAIL,
            auth_level=AuthLevel.BASIC,
            role="user",
            status=UserStatus.ACTIVE,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Clean up verification markers
        VerificationCodeStore.delete(f"email:verified:{email}")

        # Issue tokens
        access_token, refresh_token = UserService._issue_token_pair(db, user)

        # Build profile so frontend can cache user info immediately
        profile = UserService._build_profile(user, db)

        return {
            "user_id": user.id,
            "token": access_token,
            "refresh_token": refresh_token,
            "expires_in": 7200,
            "user": profile,
        }

    # ==================================================================
    # Login & Token Management
    # ==================================================================

    @staticmethod
    def login(db: Session, data: LoginRequest) -> dict:
        # Detect email vs phone: email contains '@', phone is 11 digits
        is_email = "@" in data.phone

        if is_email:
            user = db.query(User).filter(User.email == data.phone.lower().strip()).first()
        else:
            user = db.query(User).filter(User.phone == data.phone).first()

        if data.login_type == "password":
            if user is None or not verify_password(
                data.password or "", user.password_hash
            ):
                raise HTTPException(status_code=401, detail="账号或密码错误")
        elif data.login_type == "code":
            if is_email:
                key = f"email:login:{data.phone.lower().strip()}"
            else:
                key = f"login:{data.phone}"
            stored_code = VerificationCodeStore.get(key)
            if stored_code is None or stored_code != data.code:
                raise HTTPException(status_code=401, detail="验证码错误或已过期")
            VerificationCodeStore.delete(key)
            if user is None:
                raise HTTPException(status_code=404, detail="账号未注册")
        else:
            raise HTTPException(status_code=400, detail="不支持的登录方式")

        if user.status != UserStatus.ACTIVE:
            raise HTTPException(status_code=401, detail="账户已被禁用")

        # Issue tokens
        access_token, refresh_token = UserService._issue_token_pair(db, user)

        # Build profile
        profile = UserService._build_profile(user, db)

        record_activity(db, user.id, ActivityType.LOGIN)

        # ── Points: +1 daily login (once per day) ──
        from datetime import date

        from sqlalchemy import func as sa_func

        today = date.today()
        already_awarded = db.query(PointsHistory).filter(
            PointsHistory.user_id == user.id,
            PointsHistory.reason == "daily_login",
            sa_func.date(PointsHistory.created_at) == today,
        ).first() is not None
        if not already_awarded:
            award_points(db, user.id, 1, "daily_login")

        db.commit()

        return {
            "user_id": user.id,
            "token": access_token,
            "refresh_token": refresh_token,
            "expires_in": 7200,  # 2 hours
            "user": profile,
        }

    @staticmethod
    def refresh_token(raw_refresh_token: str, db: Session) -> dict:
        """Validate refresh token, rotate (revoke old, issue new pair)."""
        token_hash = hash_refresh_token(raw_refresh_token)

        stored = (
            db.query(RefreshToken)
            .filter(RefreshToken.token_hash == token_hash)
            .first()
        )

        if stored is None:
            raise HTTPException(status_code=401, detail="Refresh Token无效")

        if stored.is_revoked:
            # Potential token reuse — revoke all tokens for this user
            db.query(RefreshToken).filter(
                RefreshToken.user_id == stored.user_id
            ).update({"is_revoked": True})
            db.commit()
            raise HTTPException(status_code=401, detail="Refresh Token已被撤销")

        if stored.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
            raise HTTPException(status_code=401, detail="Refresh Token已过期")

        # Revoke the old token (rotation)
        stored.is_revoked = True
        db.commit()

        # Issue new pair
        user = db.query(User).filter(User.id == stored.user_id).first()
        if user is None or user.status != UserStatus.ACTIVE:
            raise HTTPException(status_code=401, detail="用户不存在或已被禁用")

        access_token, new_refresh_token = UserService._issue_token_pair(db, user)

        return {
            "token": access_token,
            "refresh_token": new_refresh_token,
            "expires_in": 7200,
        }

    # ==================================================================
    # Profile Management
    # ==================================================================

    @staticmethod
    def get_profile(db: Session, user: User) -> dict:
        return UserService._build_profile(user, db)

    @staticmethod
    def update_profile(db: Session, user: User, data: UpdateProfileRequest) -> None:
        if data.nickname is not None:
            user.nickname = data.nickname
        if data.bio is not None:
            user.bio = data.bio
        if data.avatar_url is not None:
            user.avatar_url = data.avatar_url
        if data.investment_tags is not None:
            user.investment_tags = data.investment_tags
        if data.follow_markets is not None:
            user.follow_markets = data.follow_markets
        if data.risk_preference is not None:
            user.risk_level = RiskLevel(data.risk_preference)

        db.commit()
        db.refresh(user)

    # ==================================================================
    # Certification & Risk Assessment
    # ==================================================================

    @staticmethod
    def submit_certification(
        db: Session, user: User, data: CertificationRequest
    ) -> dict:
        """Persist a certification application to the database.

        In production the PII fields (real_name, id_number) MUST be
        AES-256 encrypted before storage.  For the course project they
        are stored as-is to match the schema contract.
        """
        cert = Certification(
            user_id=user.id,
            real_name=data.real_name,
            id_number=data.id_number,
            id_card_front=data.id_card_front,
            id_card_back=data.id_card_back,
            status=CertificationStatus.PENDING,
        )
        db.add(cert)
        db.commit()
        db.refresh(cert)

        return {"status": "pending", "certification_id": cert.id}

    @staticmethod
    def submit_professional_certification(
        db: Session, user: User, data: ProfessionalCertificationRequest
    ) -> dict:
        """Submit a professional certification application with qualification documents."""
        # Check for existing pending professional certification
        existing = (
            db.query(ProfessionalCertification)
            .filter(
                ProfessionalCertification.user_id == user.id,
                ProfessionalCertification.status == ProfessionalCertStatus.PENDING,
            )
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=409,
                detail="已有待审核的专业认证申请，请等待审核结果",
            )

        cert = ProfessionalCertification(
            user_id=user.id,
            qualification_docs=[doc.model_dump() for doc in data.qualification_docs],
            description=data.description,
            status=ProfessionalCertStatus.PENDING,
        )
        db.add(cert)
        db.commit()
        db.refresh(cert)
        return {"status": "pending", "certification_id": cert.id}

    @staticmethod
    def submit_risk_assessment(
        db: Session, user: User, data: RiskAssessmentRequest
    ) -> dict:
        """Persist risk assessment result and update the user's risk_level."""
        # ── Validation ────────────────────────────────────────────
        valid_choices = {"A", "B", "C", "D", "E"}
        for qa in data.answers:
            if qa.answer.upper() not in valid_choices:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "code": 1001,
                        "message": (
                            f"题目 {qa.question_id} 的答案 '{qa.answer}' 无效，"
                            "只能为 A/B/C/D/E"
                        ),
                    },
                )

        total_questions = data.total_questions or len(data.answers)
        if len(data.answers) != total_questions:
            raise HTTPException(
                status_code=400,
                detail={
                    "code": 1002,
                    "message": (
                        f"问卷不完整：需要 {total_questions} 道题，"
                        f"收到 {len(data.answers)} 道"
                    ),
                },
            )

        # ── Scoring ──────────────────────────────────────────────
        score = UserService._calculate_risk_score(data.answers)

        if score <= 33:
            risk_level = RiskLevelEnum.CONSERVATIVE
            suggestion = (
                "您属于保守型投资者。建议以低风险产品为主，"
                "如货币基金、国债等，控制股票类资产比例在20%以内。"
            )
        elif score <= 66:
            risk_level = RiskLevelEnum.MODERATE
            suggestion = (
                "您属于中等风险承受型投资者。建议均衡配置股票、"
                "基金和固定收益类产品，可适当参与指数基金定投。"
            )
        else:
            risk_level = RiskLevelEnum.AGGRESSIVE
            suggestion = (
                "您属于进取型投资者。可承受较高波动，适合配置"
                "较高比例的权益类资产，但需注意分散投资风险。"
            )

        # Persist the assessment record
        assessment = RiskAssessment(
            user_id=user.id,
            answers=[qa.model_dump() for qa in data.answers],
            total_questions=total_questions,
            score=score,
            max_score=100,
            risk_level=risk_level,
            suggestion=suggestion,
        )
        db.add(assessment)

        # Update the user's risk_level
        risk_user_map = {
            RiskLevelEnum.CONSERVATIVE: RiskLevel.CONSERVATIVE,
            RiskLevelEnum.MODERATE: RiskLevel.MODERATE,
            RiskLevelEnum.AGGRESSIVE: RiskLevel.AGGRESSIVE,
        }
        user.risk_level = risk_user_map[risk_level]
        db.commit()
        db.refresh(assessment)

        return {
            "assessment_id": assessment.id,
            "risk_level": risk_level.value,
            "score": score,
            "max_score": 100,
            "suggestion": suggestion,
        }

    @staticmethod
    def get_risk_questions() -> list[dict]:
        """Return the static list of risk assessment questions."""
        return [q.model_dump() for q in RISK_QUESTIONS]

    @staticmethod
    def get_risk_assessment_history(
        db: Session,
        user: User,
        page: int = 1,
        size: int = 20,
    ) -> dict:
        """Return paginated risk assessment history for a user."""
        query = (
            db.query(RiskAssessment)
            .filter(RiskAssessment.user_id == user.id)
            .order_by(RiskAssessment.created_at.desc())
        )

        total = query.count()
        items = query.offset((page - 1) * size).limit(size).all()

        history_items = [
            RiskHistoryItem(
                id=a.id,
                score=a.score,
                risk_level=a.risk_level.value,
                total_questions=a.total_questions,
                created_at=a.created_at,
            )
            for a in items
        ]

        return PaginatedData(
            items=history_items,
            total=total,
            page=page,
            size=size,
        ).model_dump()

    # ==================================================================
    # Internal Helpers
    # ==================================================================

    @staticmethod
    def _issue_token_pair(db: Session, user: User) -> tuple[str, str]:
        """Create access + refresh tokens, persist the refresh token hash.

        Returns ``(access_token, refresh_token_raw)``.
        """
        access_token = create_access_token(data={
            "sub": str(user.id),
            "role": user.role.value if hasattr(user.role, "value") else str(user.role),
            "auth_level": user.auth_level.value if hasattr(user.auth_level, "value") else str(user.auth_level),
        })

        raw_rt, rt_hash, expires_at = create_refresh_token_record(user.id)

        rt_record = RefreshToken(
            user_id=user.id,
            token_hash=rt_hash,
            expires_at=expires_at,
            is_revoked=False,
        )
        db.add(rt_record)
        db.commit()

        return access_token, raw_rt

    @staticmethod
    def _build_profile(user: User, db: Session) -> UserProfile:
        posts_count = 0
        elite_posts = 0

        try:
            from sqlalchemy import text

            result = db.execute(
                text("SELECT COUNT(*) as cnt FROM posts WHERE user_id = :uid"),
                {"uid": user.id},
            ).first()
            if result:
                posts_count = result[0] or 0
        except Exception:
            posts_count = 0

        achievements = Achievements(
            posts_count=posts_count,
            elite_posts=elite_posts,
            influence_score=posts_count * 10,
            badges=["新手入门"] if posts_count > 0 else [],
        )

        profile = UserProfile(
            id=user.id,
            nickname=user.nickname,
            avatar_url=user.avatar_url,
            bio=user.bio,
            phone=user.phone,
            email=user.email,
            role=user.role.value if hasattr(user.role, "value") else str(user.role),
            auth_level=user.auth_level.value
            if hasattr(user.auth_level, "value")
            else str(user.auth_level),
            is_professional=user.is_professional,
            risk_level=user.risk_level.value
            if user.risk_level and hasattr(user.risk_level, "value")
            else None,
            investment_tags=user.investment_tags,
            follow_markets=user.follow_markets,
            achievements=achievements,
            points=user.points or 0,
            level=user.level or 1,
            privacy_settings=user.privacy_settings,
            created_at=user.created_at.replace(tzinfo=timezone.utc)
            if user.created_at
            else None,
        )
        return profile

    @staticmethod
    def _calculate_risk_score(answers) -> int:
        if not answers:
            return 50

        raw_score = 0
        max_possible = 0
        for qa in answers:
            choice = qa.answer.upper()
            letter_scores = {"A": 1, "B": 2, "C": 3, "D": 4, "E": 5}
            raw_score += letter_scores.get(choice, 3)
            max_possible += 5

        if max_possible == 0:
            return 50

        normalized = int((raw_score / max_possible) * 100)
        return max(0, min(100, normalized))
