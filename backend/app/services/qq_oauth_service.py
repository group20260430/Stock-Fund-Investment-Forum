import json
import secrets
from urllib.parse import parse_qs, urlencode

import httpx
import jwt
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_password_hash
from app.models.oauth import OAuthAccount, OAuthProvider
from app.models.user import AuthLevel, RegisterType, User, UserStatus
from app.services.user_service import UserService


QQ_AUTHORIZE_URL = "https://graph.qq.com/oauth2.0/authorize"
QQ_TOKEN_URL = "https://graph.qq.com/oauth2.0/token"
QQ_OPENID_URL = "https://graph.qq.com/oauth2.0/me"
QQ_USER_INFO_URL = "https://graph.qq.com/user/get_user_info"


class QQOAuthService:
    @staticmethod
    def build_authorize_url(redirect: str | None = None) -> str:
        QQOAuthService._ensure_configured()
        state = QQOAuthService._make_state(redirect)
        params = {
            "response_type": "code",
            "client_id": settings.qq_oauth_app_id,
            "redirect_uri": settings.qq_oauth_redirect_uri,
            "state": state,
        }
        return f"{QQ_AUTHORIZE_URL}?{urlencode(params)}"

    @staticmethod
    async def handle_callback(db: Session, code: str, state: str | None) -> dict:
        QQOAuthService._ensure_configured()
        redirect = QQOAuthService._parse_state(state)
        access_token = await QQOAuthService._fetch_access_token(code)
        openid_payload = await QQOAuthService._fetch_openid(access_token)
        openid = openid_payload.get("openid")
        if not openid:
            raise HTTPException(status_code=502, detail="QQ 未返回 openid")

        profile = await QQOAuthService._fetch_user_info(access_token, openid)
        user = QQOAuthService._find_or_create_user(db, openid, openid_payload.get("unionid"), profile)
        token, refresh_token = UserService._issue_token_pair(db, user)
        return {
            "token": token,
            "refresh_token": refresh_token,
            "expires_in": 7200,
            "user": UserService._build_profile(user, db),
            "redirect": redirect or "/",
        }

    @staticmethod
    def build_frontend_redirect(result: dict) -> str:
        fragment = urlencode(
            {
                "token": result["token"],
                "refresh_token": result["refresh_token"],
                "expires_in": str(result["expires_in"]),
                "redirect": result.get("redirect") or "/",
            }
        )
        return f"{settings.frontend_base_url.rstrip('/')}/oauth/qq/callback#{fragment}"

    @staticmethod
    def _ensure_configured() -> None:
        if not settings.qq_oauth_app_id or not settings.qq_oauth_app_key:
            raise HTTPException(status_code=500, detail="QQ 登录尚未配置 APP ID / APP Key")

    @staticmethod
    def _make_state(redirect: str | None) -> str:
        payload = {
            "type": "qq_oauth_state",
            "nonce": secrets.token_urlsafe(12),
            "redirect": redirect or "/",
        }
        return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

    @staticmethod
    def _parse_state(state: str | None) -> str:
        if not state:
            return "/"
        try:
            payload = jwt.decode(state, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        except jwt.InvalidTokenError as exc:
            raise HTTPException(status_code=400, detail="QQ 登录 state 无效") from exc
        if payload.get("type") != "qq_oauth_state":
            raise HTTPException(status_code=400, detail="QQ 登录 state 类型错误")
        redirect = str(payload.get("redirect") or "/")
        return redirect if redirect.startswith("/") else "/"

    @staticmethod
    async def _fetch_access_token(code: str) -> str:
        params = {
            "grant_type": "authorization_code",
            "client_id": settings.qq_oauth_app_id,
            "client_secret": settings.qq_oauth_app_key,
            "code": code,
            "redirect_uri": settings.qq_oauth_redirect_uri,
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(QQ_TOKEN_URL, params=params)
        data = parse_qs(response.text)
        if "access_token" not in data:
            raise HTTPException(status_code=502, detail=f"QQ token 获取失败: {response.text}")
        return data["access_token"][0]

    @staticmethod
    async def _fetch_openid(access_token: str) -> dict:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(QQ_OPENID_URL, params={"access_token": access_token})
        text = response.text.strip()
        if text.startswith("callback("):
            text = text.removeprefix("callback(").removesuffix(");").strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=502, detail=f"QQ openid 解析失败: {response.text}") from exc

    @staticmethod
    async def _fetch_user_info(access_token: str, openid: str) -> dict:
        params = {
            "access_token": access_token,
            "oauth_consumer_key": settings.qq_oauth_app_id,
            "openid": openid,
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(QQ_USER_INFO_URL, params=params)
        data = response.json()
        if data.get("ret") != 0:
            raise HTTPException(status_code=502, detail=data.get("msg") or "QQ 用户信息获取失败")
        return data

    @staticmethod
    def _find_or_create_user(db: Session, openid: str, unionid: str | None, profile: dict) -> User:
        account = db.query(OAuthAccount).filter(
            OAuthAccount.provider == OAuthProvider.QQ,
            OAuthAccount.openid == openid,
        ).first()
        if account:
            account.nickname = profile.get("nickname") or account.nickname
            account.avatar_url = profile.get("figureurl_qq_2") or profile.get("figureurl_qq_1") or account.avatar_url
            account.raw_profile = profile
            db.commit()
            return account.user

        nickname = (profile.get("nickname") or "QQ用户").strip()[:50]
        avatar_url = profile.get("figureurl_qq_2") or profile.get("figureurl_qq_1") or profile.get("figureurl_2")
        user = User(
            phone=None,
            email=None,
            password_hash=get_password_hash(secrets.token_urlsafe(32)),
            nickname=nickname,
            avatar_url=avatar_url,
            register_type=RegisterType.QQ,
            auth_level=AuthLevel.BASIC,
            status=UserStatus.ACTIVE,
        )
        db.add(user)
        db.flush()
        db.add(
            OAuthAccount(
                user_id=user.id,
                provider=OAuthProvider.QQ,
                openid=openid,
                unionid=unionid,
                nickname=nickname,
                avatar_url=avatar_url,
                raw_profile=profile,
            )
        )
        db.commit()
        db.refresh(user)
        return user
