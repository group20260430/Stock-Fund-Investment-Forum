"""Weibo OAuth service — dev mode (simulated) and real mode."""
import secrets

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_password_hash
from app.models.oauth import OAuthAccount, OAuthProvider
from app.models.user import AuthLevel, RegisterType, User, UserStatus
from app.services.user_service import UserService


DEV_WEIBO_PROFILE = {
    "idstr": "dev_weibo_uid",
    "screen_name": "微博用户",
    "avatar_large": "https://example.com/weibo_avatar.jpg",
    "gender": "m",
    "location": "广东 深圳",
    "description": "模拟微博用户",
}


class WeiboOAuthService:
    """Weibo OAuth (微博登录) service with dev mode."""

    @staticmethod
    def build_authorize_url(redirect: str | None = None) -> str:
        if settings.oauth_dev_mode:
            state = WeiboOAuthService._make_state(redirect)
            from urllib.parse import urlencode
            params = urlencode({"code": "dev_weibo_code", "state": state, "redirect": redirect or "/"})
            return f"{settings.frontend_base_url.rstrip('/')}/auth/weibo/callback?{params}"
        if not settings.weibo_oauth_app_id:
            raise HTTPException(status_code=500, detail="微博登录尚未配置 APP ID")
        state = WeiboOAuthService._make_state(redirect)
        from urllib.parse import urlencode
        params = {
            "client_id": settings.weibo_oauth_app_id,
            "redirect_uri": settings.weibo_oauth_redirect_uri,
            "response_type": "code",
            "state": state,
        }
        return f"https://api.weibo.com/oauth2/authorize?{urlencode(params)}"

    @staticmethod
    async def handle_callback(db: Session, code: str, state: str | None) -> dict:
        redirect = WeiboOAuthService._parse_state(state)

        if settings.oauth_dev_mode:
            profile = dict(DEV_WEIBO_PROFILE)
            profile["idstr"] = f"dev_weibo_{secrets.token_hex(8)}"
        else:
            access_token_data = await WeiboOAuthService._fetch_access_token(code)
            profile = await WeiboOAuthService._fetch_user_info(access_token_data["access_token"], access_token_data["uid"])

        uid = str(profile.get("idstr") or profile.get("id", ""))
        if not uid:
            raise HTTPException(status_code=502, detail="微博未返回用户 ID")
        user = WeiboOAuthService._find_or_create_user(db, uid, profile)
        token, refresh_token = UserService._issue_token_pair(db, user)
        return {
            "token": token, "refresh_token": refresh_token, "expires_in": 7200,
            "user": UserService._build_profile(user, db),
            "redirect": redirect or "/",
        }

    @staticmethod
    def build_frontend_redirect(result: dict) -> str:
        from urllib.parse import urlencode
        fragment = urlencode({
            "token": result["token"], "refresh_token": result["refresh_token"],
            "expires_in": str(result["expires_in"]),
            "redirect": result.get("redirect") or "/",
        })
        return f"{settings.frontend_base_url.rstrip('/')}/oauth/weibo/callback#{fragment}"

    @staticmethod
    def _make_state(redirect: str | None) -> str:
        import jwt as pyjwt
        payload = {"type": "weibo_oauth_state", "nonce": secrets.token_urlsafe(12), "redirect": redirect or "/"}
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
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                "https://api.weibo.com/oauth2/access_token",
                data={
                    "client_id": settings.weibo_oauth_app_id,
                    "client_secret": settings.weibo_oauth_app_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": settings.weibo_oauth_redirect_uri,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
        data = response.json()
        if "access_token" not in data:
            raise HTTPException(status_code=502, detail=f"微博 token 获取失败: {response.text}")
        return data

    @staticmethod
    async def _fetch_user_info(access_token: str, uid: str) -> dict:
        import httpx
        params = {"access_token": access_token, "uid": uid}
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get("https://api.weibo.com/2/users/show.json", params=params)
        data = response.json()
        if "idstr" not in data and "id" not in data:
            raise HTTPException(status_code=502, detail=f"微博用户信息获取失败: {response.text}")
        return data

    @staticmethod
    def _find_or_create_user(db: Session, uid: str, profile: dict) -> User:
        account = db.query(OAuthAccount).filter(
            OAuthAccount.provider == OAuthProvider.WEIBO,
            OAuthAccount.openid == uid,
        ).first()
        if account:
            account.nickname = profile.get("screen_name") or account.nickname
            account.avatar_url = profile.get("avatar_large") or account.avatar_url
            account.raw_profile = profile
            db.commit()
            return account.user

        nickname = (profile.get("screen_name") or "微博用户").strip()[:50]
        avatar_url = profile.get("avatar_large")
        user = User(
            phone=None, email=None,
            password_hash=get_password_hash(secrets.token_urlsafe(32)),
            nickname=nickname, avatar_url=avatar_url,
            register_type=RegisterType.WEIBO,
            auth_level=AuthLevel.BASIC,
            status=UserStatus.ACTIVE,
        )
        db.add(user)
        db.flush()
        db.add(OAuthAccount(
            user_id=user.id, provider=OAuthProvider.WEIBO,
            openid=uid, unionid=None,
            nickname=nickname, avatar_url=avatar_url, raw_profile=profile,
        ))
        db.commit()
        db.refresh(user)
        return user
