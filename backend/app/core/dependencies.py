"""FastAPI dependencies: auth extraction, rate limiting, role guards."""

import time

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User, UserRole, UserStatus

security = HTTPBearer()
optional_security = HTTPBearer(auto_error=False)


# ---------------------------------------------------------------------------
# Rate limiter
# ---------------------------------------------------------------------------

class RateLimiter:
    """Simple in-memory sliding-window rate limiter."""

    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._store: dict[str, list[float]] = {}

    async def __call__(self, request: Request) -> None:
        client_ip = request.headers.get(
            "x-forwarded-for",
            request.client.host if request.client else "unknown",
        )
        now = time.time()

        if client_ip not in self._store:
            self._store[client_ip] = []

        cutoff = now - self.window_seconds
        self._store[client_ip] = [t for t in self._store[client_ip] if t > cutoff]

        if len(self._store[client_ip]) >= self.max_requests:
            raise HTTPException(
                status_code=429,
                detail="请求过于频繁，请稍后再试",
            )

        self._store[client_ip].append(now)


class UserRateLimiter:
    """Per-user in-memory sliding-window rate limiter for content actions."""

    def __init__(self, max_requests: int, window_seconds: int, action_name: str = "操作"):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.action_name = action_name
        self._store: dict[int, list[float]] = {}

    def check(self, user_id: int) -> None:
        """Raise HTTPException(429) if user exceeded the limit."""
        now = time.time()
        if user_id not in self._store:
            self._store[user_id] = []
        cutoff = now - self.window_seconds
        self._store[user_id] = [t for t in self._store[user_id] if t > cutoff]
        if len(self._store[user_id]) >= self.max_requests:
            raise HTTPException(
                status_code=429,
                detail=f"{self.action_name}过于频繁，请稍后再试",
            )
        self._store[user_id].append(now)


# ---------------------------------------------------------------------------
# Auth dependencies
# ---------------------------------------------------------------------------


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """Extract and validate the Bearer token, return the authenticated user.

    Raises ``HTTPException(401)`` when the token is missing, expired, or
    the user does not exist / is disabled.
    """
    token = credentials.credentials
    payload = decode_access_token(token)
    try:
        user_id = int(payload["sub"])
    except (KeyError, ValueError, TypeError):
        raise HTTPException(status_code=401, detail="Token无效") from None

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=401, detail="用户不存在或已被禁用")
    if user.status != UserStatus.ACTIVE:
        raise HTTPException(status_code=401, detail="账户已被禁用")

    return user


def get_optional_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(optional_security),
    db: Session = Depends(get_db),
) -> User | None:
    """Return the current user when a valid token is supplied, otherwise anonymous."""
    if credentials is None:
        return None
    try:
        return get_current_user(credentials, db)
    except HTTPException:
        return None


def get_current_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Require the authenticated user to be an admin (role=``admin``)."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return current_user


def get_current_moderator(
    current_user: User = Depends(get_current_user),
) -> User:
    """Require the authenticated user to be a moderator or admin."""
    if current_user.role not in (UserRole.MODERATOR, UserRole.ADMIN):
        raise HTTPException(status_code=403, detail="需要版主或管理员权限")
    return current_user
