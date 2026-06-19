import random
import time
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password,
)
from app.models.user import AuthLevel, RiskLevel, User, UserStatus
from app.schemas.user import (
    Achievements,
    CertificationRequest,
    LoginRequest,
    RegisterRequest,
    RiskAssessmentRequest,
    SendCodeRequest,
    UpdateProfileRequest,
    UserProfile,
)


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

    # ========== Registration & Verification ==========

    @staticmethod
    def register(db: Session, data: RegisterRequest) -> dict:
        # Check duplicate phone
        existing = db.query(User).filter(User.phone == data.phone).first()
        if existing:
            raise HTTPException(status_code=409, detail="该手机号已注册")

        # Hash password
        password_hash = get_password_hash(data.password)

        # Auto-generate nickname if not provided
        nickname = data.nickname or f"用户{data.phone[-4:]}"

        # Create user
        user = User(
            phone=data.phone,
            password_hash=password_hash,
            nickname=nickname,
            avatar_url=data.avatar_url,
            auth_level=AuthLevel.NONE,
            role="user",
            status=UserStatus.ACTIVE,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Generate JWT
        token = create_access_token(data={"sub": str(user.id)})

        return {"user_id": user.id, "token": token}

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

        # Simulated SMS
        print(f"[SIMULATED SMS] Code for {data.phone} ({data.type}): {code}")

        return {"expire_in": 300}

    # ========== Login & Token Management ==========

    @staticmethod
    def login(db: Session, data: LoginRequest) -> dict:
        user = db.query(User).filter(User.phone == data.phone).first()

        if data.login_type == "password":
            if user is None or not verify_password(data.password or "", user.password_hash):
                raise HTTPException(status_code=401, detail="手机号或密码错误")
        elif data.login_type == "code":
            key = f"login:{data.phone}"
            stored_code = VerificationCodeStore.get(key)
            if stored_code is None or stored_code != data.code:
                raise HTTPException(status_code=401, detail="验证码错误或已过期")
            VerificationCodeStore.delete(key)
            if user is None:
                # Auto-register via code login? No — API spec says user must exist.
                raise HTTPException(status_code=404, detail="该手机号未注册")
        else:
            raise HTTPException(status_code=400, detail="不支持的登录方式")

        if user.status != UserStatus.ACTIVE:
            raise HTTPException(status_code=401, detail="账户已被禁用")

        # Build token
        token = create_access_token(data={"sub": str(user.id)})
        expires_in = 86400  # 24 hours

        # Build profile
        profile = UserService._build_profile(user, db)

        return {
            "user_id": user.id,
            "token": token,
            "expires_in": expires_in,
            "user": profile,
        }

    @staticmethod
    def refresh_token(token: str) -> dict:
        payload = decode_access_token(token)
        try:
            user_id = payload["sub"]
        except KeyError:
            raise HTTPException(status_code=401, detail="Token无效")

        new_token = create_access_token(data={"sub": user_id})
        return {"token": new_token, "expires_in": 86400}

    # ========== Profile Management ==========

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

    # ========== Certification & Risk Assessment ==========

    @staticmethod
    def submit_certification(user: User, data: CertificationRequest) -> dict:
        # In a real app, this would create a certification record for admin review.
        # For this course project, return simulated "pending" status.
        print(
            f"[SIMULATED CERT] User {user.id} ({user.nickname}) submitted "
            f"cert for {data.real_name} ({data.id_number})"
        )
        return {"status": "pending"}

    @staticmethod
    def submit_risk_assessment(data: RiskAssessmentRequest) -> dict:
        score = UserService._calculate_risk_score(data.answers)

        if score <= 33:
            risk_level = "conservative"
            suggestion = "您属于保守型投资者。建议以低风险产品为主，如货币基金、国债等，控制股票类资产比例在20%以内。"
        elif score <= 66:
            risk_level = "moderate"
            suggestion = "您属于中等风险承受型投资者。建议均衡配置股票、基金和固定收益类产品，可适当参与指数基金定投。"
        else:
            risk_level = "aggressive"
            suggestion = "您属于进取型投资者。可承受较高波动，适合配置较高比例的权益类资产，但需注意分散投资风险。"

        return {
            "risk_level": risk_level,
            "score": score,
            "max_score": 100,
            "suggestion": suggestion,
        }

    # ========== Internal Helpers ==========

    @staticmethod
    def _build_profile(user: User, db: Session) -> UserProfile:
        # Count user's posts
        from app.models.user import User as U

        posts_count = 0
        elite_posts = 0

        try:
            # Only count if tables exist
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
            phone=user.phone,  # masking handled by Pydantic validator
            email=user.email,
            role=user.role.value if hasattr(user.role, "value") else str(user.role),
            auth_level=user.auth_level.value if hasattr(user.auth_level, "value") else str(user.auth_level),
            is_professional=user.is_professional,
            risk_level=user.risk_level.value if user.risk_level and hasattr(user.risk_level, "value") else None,
            investment_tags=user.investment_tags,
            follow_markets=user.follow_markets,
            achievements=achievements,
            created_at=user.created_at.replace(tzinfo=timezone.utc) if user.created_at else None,
        )
        return profile

    @staticmethod
    def _calculate_risk_score(answers) -> int:
        # Simplified risk assessment scoring
        # Each answer choice maps to a score: A=1, B=2, C=3, D=4, E=5
        # The score is normalized to 0-100 range
        if not answers:
            return 50  # default moderate

        raw_score = 0
        max_possible = 0
        for qa in answers:
            # Map the answer choice to a numeric value
            choice = qa.answer.upper()
            letter_scores = {"A": 1, "B": 2, "C": 3, "D": 4, "E": 5}
            raw_score += letter_scores.get(choice, 3)
            max_possible += 5

        if max_possible == 0:
            return 50

        normalized = int((raw_score / max_possible) * 100)
        return max(0, min(100, normalized))
