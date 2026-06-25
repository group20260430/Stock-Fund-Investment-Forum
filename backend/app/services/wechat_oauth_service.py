"""WeChat OAuth service — dev mode (simulated) and real mode.

In dev mode (oauth_dev_mode=True), the service simulates a successful OAuth
flow without calling the real WeChat API, returning a mock user profile.
This allows testing without a published WeChat OAuth app.
"""
import secrets

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_password_hash
from app.models.oauth import OAuthAccount, OAuthProvider
from app.models.user import AuthLevel, RegisterType, User, UserStatus
from app.services.user_service import UserService


# ── Dev mode mock data ─────────────────────────────────────────────────
DEV_WECHAT_PROFILE = {
    "openid": "dev_wechat_openid",
    "unionid": "dev_wechat_unionid",
    "nickname": "微信用户",
    "headimgurl": "https://example.com/wechat_avatar.png",
    "sex": 1,
    "province": "广东",
    "city": "深圳",
    "country": "中国",
}


class WeChatOAuthService:
    """WeChat OAuth (微信登录) service.

    In dev mode (settings.oauth_dev_mode is True), all methods work without
    a real WeChat app — they simulate the OAuth flow end-to-end.
    """

    @staticmethod
    def build_authorize_url(redirect: str | None = None) -> str:
        if settings.oauth_dev_mode:
            # Dev mode: simulate authorization by directly returning callback URL with mock code
            state = WeChatOAuthService._make_state(redirect)
            from urllib.parse import urlencode
            params = urlencode({"code": "dev_auth_code", "state": state, "redirect": redirect or "/"})
            return f"{settings.frontend_base_url.rstrip('/')}/auth/wechat/callback?{params}"
        if not settings.wechat_oauth_app_id:
            raise HTTPException(status_code=500, detail="微信登录尚未配置 APP ID")
        state = WeChatOAuthService._make_state(redirect)
        from urllib.parse import urlencode
        params = {
            "appid": settings.wechat_oauth_app_id,
            "redirect_uri": settings.wechat_oauth_redirect_uri,
            "response_type": "code",
            "scope": "snsapi_login",
            "state": state,
        }
        return f"https://open.weixin.qq.com/connect/qrconnect?{urlencode(params)}"

    @staticmethod
    async def handle_callback(db: Session, code: str, state: str | None) -> dict:
        redirect = WeChatOAuthService._parse_state(state)

        if settings.oauth_dev_mode:
            # Dev mode: return mock profile
            profile = dict(DEV_WECHAT_PROFILE)
            profile["openid"] = f"dev_wechat_{secrets.token_hex(8)}"
        else:
            access_token = await WeChatOAuthService._fetch_access_token(code)
            profile = await WeChatOAuthService._fetch_user_info(access_token)
            if "openid" not in profile:
                raise HTTPException(status_code=502, detail="微信未返回 openid")

        openid = profile["openid"]
        unionid = profile.get("unionid")
        user = WeChatOAuthService._find_or_create_user(db, openid, unionid, profile)
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
        from urllib.parse import urlencode
        fragment = urlencode({
            "token": result["token"],
            "refresh_token": result["refresh_token"],
            "expires_in": str(result["expires_in"]),
            "redirect": result.get("redirect") or "/",
        })
        return f"{settings.frontend_base_url.rstrip('/')}/oauth/wechat/callback#{fragment}"

    @staticmethod
    def _make_state(redirect: str | None) -> str:
        import jwt as pyjwt
        payload = {
            "type": "wechat_oauth_state",
            "nonce": secrets.token_urlsafe(12),
            "redirect": redirect or "/",
        }
        return pyjwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

    @staticmethod
    def _parse_state(state: str | None) -> str:
        if not state:
            return "/"
        import jwt as pyjwt
        try:
            payload = pyjwt.decode(state, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        except pyjwt.InvalidTokenError:
            return "/"
        redirect = str(payload.get("redirect") or "/")
        return redirect if redirect.startswith("/") else "/"

    @staticmethod
    async def _fetch_access_token(code: str) -> dict:
        import httpx
        params = {
            "appid": settings.wechat_oauth_app_id,
            "secret": settings.wechat_oauth_app_secret,
            "code": code,
            "grant_type": "authorization_code",
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get("https://api.weixin.qq.com/sns/oauth2/access_token", params=params)
        data = response.json()
        if "access_token" not in data:
            raise HTTPException(status_code=502, detail=f"微信 token 获取失败: {response.text}")
        return data

    @staticmethod
    async def _fetch_user_info(access_token_data: dict) -> dict:
        import httpx
        params = {
            "access_token": access_token_data["access_token"],
            "openid": access_token_data["openid"],
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get("https://api.weixin.qq.com/sns/userinfo", params=params)
        data = response.json()
        if "openid" not in data:
            raise HTTPException(status_code=502, detail=f"微信用户信息获取失败: {response.text}")
        return data

    @staticmethod
    def _find_or_create_user(db: Session, openid: str, unionid: str | None, profile: dict) -> User:
        account = db.query(OAuthAccount).filter(
            OAuthAccount.provider == OAuthProvider.WECHAT,
            OAuthAccount.openid == openid,
        ).first()
        if account:
            account.nickname = profile.get("nickname") or account.nickname
            account.avatar_url = profile.get("headimgurl") or account.avatar_url
            account.raw_profile = profile
            db.commit()
            return account.user

        nickname = (profile.get("nickname") or "微信用户").strip()[:50]
        avatar_url = profile.get("headimgurl")
        user = User(
            phone=None, email=None,
            password_hash=get_password_hash(secrets.token_urlsafe(32)),
            nickname=nickname, avatar_url=avatar_url,
            register_type=RegisterType.WECHAT,
            auth_level=AuthLevel.BASIC,
            status=UserStatus.ACTIVE,
        )
        db.add(user)
        db.flush()
        db.add(OAuthAccount(
            user_id=user.id, provider=OAuthProvider.WECHAT,
            openid=openid, unionid=unionid,
            nickname=nickname, avatar_url=avatar_url, raw_profile=profile,
        ))
        db.commit()
        db.refresh(user)
        return user
