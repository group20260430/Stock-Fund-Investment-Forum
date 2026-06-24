"""Unit tests for UserService.register() — registration method."""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.models.user import RegisterType
from app.schemas.user import RegisterRequest
from app.services.user_service import UserService


# Mock profile to avoid pydantic validation issues with real User objects
MOCK_PROFILE = {
    "id": 1,
    "nickname": "test_user",
    "avatar_url": None,
    "bio": None,
    "phone": "138****8000",
    "email": None,
    "role": "user",
    "auth_level": "basic",
    "is_professional": False,
    "risk_level": None,
    "investment_tags": None,
    "follow_markets": None,
    "achievements": {"posts_count": 0, "elite_posts": 0, "influence_score": 0, "badges": []},
    "points": 0,
    "level": 1,
    "privacy_settings": None,
    "created_at": None,
}


class TestUserServiceRegister:
    """Tests for UserService.register()."""

    # ── Normal register ───────────────────────────────────────────────────

    def test_normal_register_returns_full_response(self, db):
        """正常注册：完整请求 → 验证返回 user_id、token、refresh_token、expires_in、profile."""
        # No duplicate user
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        db.query.return_value = mock_q
        mock_q.first.return_value = None

        with patch(
            "app.services.user_service.UserService._build_profile",
            return_value=MOCK_PROFILE,
        ), patch(
            "app.services.user_service.get_password_hash"
        ) as mock_gph, patch(
            "app.services.user_service.create_access_token"
        ) as mock_cat, patch(
            "app.services.user_service.create_refresh_token_record"
        ) as mock_crtr:
            mock_gph.return_value = "$2b$12$hashedpassword12345678901234567890"
            mock_cat.return_value = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.access_token"
            mock_crtr.return_value = (
                "raw_refresh_token_64chars_hex",
                "sha256_hash_of_token",
                datetime.now(timezone.utc) + timedelta(days=7),
            )

            req = RegisterRequest(
                phone="13800138000",
                password="TestPass123",
                nickname="test_user",
            )
            result = UserService.register(db, req)

        # Verify response structure (user_id may be None since DB is mocked and can't assign ID)
        assert "user_id" in result
        assert result["token"] == "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.access_token"
        assert result["refresh_token"] == "raw_refresh_token_64chars_hex"
        assert result["expires_in"] == 7200
        assert result["user"] == MOCK_PROFILE

    # ── Duplicate phone ───────────────────────────────────────────────────

    def test_duplicate_phone_raises_409(self, db):
        """同一 phone 注册两次 → 第一次成功，第二次 409."""
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        db.query.return_value = mock_q
        # Existing user found
        mock_user = MagicMock()
        mock_q.first.return_value = mock_user

        req = RegisterRequest(phone="13800138000", password="TestPass123")
        with pytest.raises(HTTPException) as exc_info:
            UserService.register(db, req)
        assert exc_info.value.status_code == 409
        assert "已注册" in exc_info.value.detail

    # ── No nickname auto-generation ───────────────────────────────────────

    def test_no_nickname_auto_generates(self, db):
        """无昵称注册：不传 nickname → 自动生成 "用户+手机尾号"."""
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        db.query.return_value = mock_q
        mock_q.first.return_value = None

        with patch(
            "app.services.user_service.UserService._build_profile",
            return_value=MOCK_PROFILE,
        ), patch(
            "app.services.user_service.get_password_hash"
        ) as mock_gph, patch(
            "app.services.user_service.create_access_token"
        ) as mock_cat, patch(
            "app.services.user_service.create_refresh_token_record"
        ) as mock_crtr:
            mock_gph.return_value = "hashed"
            mock_cat.return_value = "access_token"
            mock_crtr.return_value = ("raw", "hash", datetime.now(timezone.utc) + timedelta(days=7))

            req = RegisterRequest(
                phone="13800138000",
                password="TestPass123",
                # nickname not provided → auto-gen
            )
            UserService.register(db, req)

        # Check that db.add was called and the user has auto-generated nickname
        db.add.assert_called()
        # The first db.add call is for the User
        first_add_call = db.add.call_args_list[0]
        user_arg = first_add_call[0][0]
        assert user_arg.nickname is not None
        assert user_arg.nickname.startswith("用户")

    # ── Invalid register_type fallback ────────────────────────────────────

    def test_valid_register_type_phone(self, db):
        """明确传 register_type="phone" → User.register_type = RegisterType.PHONE."""
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        db.query.return_value = mock_q
        mock_q.first.return_value = None

        with patch(
            "app.services.user_service.UserService._build_profile",
            return_value=MOCK_PROFILE,
        ), patch(
            "app.services.user_service.get_password_hash"
        ) as mock_gph, patch(
            "app.services.user_service.create_access_token"
        ) as mock_cat, patch(
            "app.services.user_service.create_refresh_token_record"
        ) as mock_crtr:
            mock_gph.return_value = "hashed"
            mock_cat.return_value = "access_token"
            mock_crtr.return_value = ("raw", "hash", datetime.now(timezone.utc) + timedelta(days=7))

            req = RegisterRequest(
                phone="13800138000",
                password="TestPass123",
                register_type="phone",
            )
            UserService.register(db, req)

        first_add_call = db.add.call_args_list[0]
        user_arg = first_add_call[0][0]
        assert user_arg.register_type == RegisterType.PHONE

    def test_valid_register_type_wechat(self, db):
        """明确传 register_type="wechat" → User.register_type = RegisterType.WECHAT."""
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        db.query.return_value = mock_q
        mock_q.first.return_value = None

        with patch(
            "app.services.user_service.UserService._build_profile",
            return_value=MOCK_PROFILE,
        ), patch(
            "app.services.user_service.get_password_hash"
        ) as mock_gph, patch(
            "app.services.user_service.create_access_token"
        ) as mock_cat, patch(
            "app.services.user_service.create_refresh_token_record"
        ) as mock_crtr:
            mock_gph.return_value = "hashed"
            mock_cat.return_value = "access_token"
            mock_crtr.return_value = ("raw", "hash", datetime.now(timezone.utc) + timedelta(days=7))

            req = RegisterRequest(
                phone="13800138000",
                password="TestPass123",
                register_type="wechat",
            )
            UserService.register(db, req)

        first_add_call = db.add.call_args_list[0]
        user_arg = first_add_call[0][0]
        assert user_arg.register_type == RegisterType.WECHAT

    # ── With avatar_url ───────────────────────────────────────────────────

    def test_with_avatar_url(self, db):
        """带 avatar_url 注册：验证 avatar_url 正确存入."""
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        db.query.return_value = mock_q
        mock_q.first.return_value = None

        with patch(
            "app.services.user_service.UserService._build_profile",
            return_value=MOCK_PROFILE,
        ), patch(
            "app.services.user_service.get_password_hash"
        ) as mock_gph, patch(
            "app.services.user_service.create_access_token"
        ) as mock_cat, patch(
            "app.services.user_service.create_refresh_token_record"
        ) as mock_crtr:
            mock_gph.return_value = "hashed"
            mock_cat.return_value = "access_token"
            mock_crtr.return_value = ("raw", "hash", datetime.now(timezone.utc) + timedelta(days=7))

            req = RegisterRequest(
                phone="13800138000",
                password="TestPass123",
                avatar_url="https://example.com/avatar.png",
            )
            UserService.register(db, req)

        first_add_call = db.add.call_args_list[0]
        user_arg = first_add_call[0][0]
        assert user_arg.avatar_url == "https://example.com/avatar.png"

    # ── Mock password_hash verification ───────────────────────────────────

    def test_get_password_hash_called(self, db):
        """验证 get_password_hash 被调用且结果存入 user."""
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        db.query.return_value = mock_q
        mock_q.first.return_value = None

        with patch(
            "app.services.user_service.UserService._build_profile",
            return_value=MOCK_PROFILE,
        ), patch(
            "app.services.user_service.get_password_hash"
        ) as mock_gph, patch(
            "app.services.user_service.create_access_token"
        ) as mock_cat, patch(
            "app.services.user_service.create_refresh_token_record"
        ) as mock_crtr:
            mock_gph.return_value = "$2b$12$hashed_for_test"
            mock_cat.return_value = "access_token"
            mock_crtr.return_value = ("raw", "hash", datetime.now(timezone.utc) + timedelta(days=7))

            req = RegisterRequest(phone="13800138000", password="MySecurePass1")
            UserService.register(db, req)

        mock_gph.assert_called_once_with("MySecurePass1")
        first_add_call = db.add.call_args_list[0]
        user_arg = first_add_call[0][0]
        assert user_arg.password_hash == "$2b$12$hashed_for_test"

    # ── Mock Token issuance ───────────────────────────────────────────────

    def test_token_functions_called(self, db):
        """验证 create_access_token 和 create_refresh_token_record 被调用."""
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        db.query.return_value = mock_q
        mock_q.first.return_value = None

        with patch(
            "app.services.user_service.UserService._build_profile",
            return_value=MOCK_PROFILE,
        ), patch(
            "app.services.user_service.get_password_hash"
        ) as mock_gph, patch(
            "app.services.user_service.create_access_token"
        ) as mock_cat, patch(
            "app.services.user_service.create_refresh_token_record"
        ) as mock_crtr:
            mock_gph.return_value = "hashed"
            mock_cat.return_value = "access_token_xyz"
            mock_crtr.return_value = ("raw_rt", "rt_hash", datetime.now(timezone.utc) + timedelta(days=7))

            req = RegisterRequest(phone="13800138000", password="TestPass123")
            UserService.register(db, req)

        mock_cat.assert_called_once()
        mock_crtr.assert_called_once()
        # create_access_token should receive data dict with sub, role, auth_level
        # Called as create_access_token(data={...}) with keyword argument
        call_kwargs = mock_cat.call_args.kwargs
        call_data = call_kwargs.get("data", {})
        assert "sub" in call_data
        assert "role" in call_data
        assert "auth_level" in call_data
        # auth_level should be BASIC for phone registration
        assert call_data.get("auth_level") == "basic"
