"""Security utilities: password hashing (bcrypt), JWT token creation & verification.

Access Token  — 2 hours  (architect.md §8.1)
Refresh Token — 7 days   (architect.md §8.1, db.md §3.1.5)
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt
from fastapi import HTTPException

from app.core.config import settings

# ---------------------------------------------------------------------------
# Password helpers
# ---------------------------------------------------------------------------


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against its bcrypt hash."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), hashed_password.encode("utf-8")
    )


def get_password_hash(password: str) -> str:
    """Return bcrypt hash of *password* (cost factor 12)."""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


# ---------------------------------------------------------------------------
# JWT — Access Token
# ---------------------------------------------------------------------------


def create_access_token(
    data: dict[str, Any], expires_delta: timedelta | None = None
) -> str:
    """Create a signed JWT access token.

    *data*  must contain at least ``{"sub": "<user_id>"}``.
    """
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + (
        expires_delta
        if expires_delta
        else timedelta(seconds=settings.access_token_expire_seconds)
    )
    to_encode.update({"exp": expire, "iat": now, "type": "access"})
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate an access token.

    Raises ``HTTPException(401)`` on expired / invalid tokens so callers
    (especially ``get_current_user``) do not need duplicate error handling.
    """
    try:
        payload: dict[str, Any] = jwt.decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Token类型错误")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token已过期") from None
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token无效") from None


# ---------------------------------------------------------------------------
# JWT — Refresh Token (opaque random string, SHA-256 hashed before storage)
# ---------------------------------------------------------------------------


def generate_refresh_token() -> str:
    """Return a cryptographically-secure 64-character hex refresh token."""
    return secrets.token_hex(32)


def hash_refresh_token(raw_token: str) -> str:
    """Return SHA-256 hex digest of *raw_token* (for database storage)."""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def create_refresh_token_record(user_id: int) -> tuple[str, str, datetime]:
    """Generate a refresh token and return (raw_token, token_hash, expires_at).

    Caller is responsible for persisting the hash + expires_at to the DB.
    The *raw_token* should be returned to the client exactly once.
    """
    raw = generate_refresh_token()
    token_hash = hash_refresh_token(raw)
    expires_at = datetime.now(timezone.utc) + timedelta(
        seconds=settings.refresh_token_expire_seconds
    )
    return raw, token_hash, expires_at
