"""Shared pytest fixtures for unit tests."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, PropertyMock, patch

import pytest
from sqlalchemy.orm import Session

from app.models.user import (
    AuthLevel,
    RegisterType,
    RiskLevel,
    User,
    UserRole,
    UserStatus,
)
from app.services.user_service import VerificationCodeStore


@pytest.fixture
def db():
    """Return a mock SQLAlchemy Session.

    Tests configure return values by setting attributes on the mock chain.
    Common patterns:

        # Single query → .first()
        db.query.return_value.filter.return_value.first.return_value = mock_user

        # Single query → .all()
        db.query.return_value.filter.return_value.all.return_value = [item1, item2]

        # Multi-query (different return values for each call)
        q1 = MagicMock(); q1.filter.return_value.first.return_value = result1
        q2 = MagicMock(); q2.filter.return_value.first.return_value = result2
        db.query.side_effect = [q1, q2]

        # Chained query with order_by + limit
        db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [...]
    """
    return MagicMock(spec=Session)


@pytest.fixture
def mock_user():
    """Return a minimal User-like MagicMock with all required attributes."""
    user = MagicMock(spec=User)
    user.id = 1
    user.phone = "13800138000"
    user.email = None
    user.password_hash = "$2b$12$fakehashedpassword12345678901234567890"
    user.nickname = "test_user"
    user.avatar_url = None
    user.bio = None
    user.role = UserRole.USER
    user.auth_level = AuthLevel.BASIC
    user.risk_level = None
    user.status = UserStatus.ACTIVE
    user.register_type = RegisterType.PHONE
    user.is_professional = False
    user.investment_tags = None
    user.follow_markets = None
    user.privacy_settings = None
    user.points = 0
    user.level = 1
    user.created_at = datetime.now(timezone.utc)
    user.updated_at = datetime.now(timezone.utc)
    user.ban_expires_at = None
    user.banned_reason = None
    user.followers_count = 0
    user.following_count = 0
    return user


@pytest.fixture(autouse=True)
def auto_clear_codes():
    """Clear VerificationCodeStore state before each test."""
    VerificationCodeStore._codes.clear()
    yield
    VerificationCodeStore._codes.clear()


@pytest.fixture(autouse=True)
def patch_settings():
    """Ensure smtp_configured is False in unit tests (dev mode).

    smtp_configured is a @property on Settings, so we patch it on the class
    using PropertyMock to avoid pydantic setattr restrictions.
    """
    from app.core.config import Settings

    with patch.object(
        Settings, "smtp_configured", new_callable=PropertyMock
    ) as mock_prop:
        mock_prop.return_value = False
        yield
