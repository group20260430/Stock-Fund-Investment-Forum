"""Unit tests for email registration flow — send_email_code, verify_email_code, register_by_email."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.models.user import AuthLevel, RegisterType, User
from app.schemas.user import EmailRegisterRequest, EmailSendCodeRequest
from app.services.user_service import UserService, VerificationCodeStore


class TestSendEmailCode:
    """Tests for UserService.send_email_code()."""

    @pytest.mark.asyncio
    async def test_register_new_email(self, db):
        """register 类型，邮箱未注册 → 成功."""
        db.query.return_value.filter.return_value.first.return_value = None
        req = EmailSendCodeRequest(email="new@test.com", type="register")

        with patch("app.services.user_service.EmailService.send_verification_code", new=AsyncMock()):
            result = await UserService.send_email_code(db, req)

        assert result["expire_in"] == 300

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, db):
        """register 类型，邮箱已注册 → 409."""
        mock_user = MagicMock(spec=User)
        db.query.return_value.filter.return_value.first.return_value = mock_user
        req = EmailSendCodeRequest(email="existing@test.com", type="register")

        with pytest.raises(HTTPException) as exc:
            await UserService.send_email_code(db, req)
        assert exc.value.status_code == 409
        assert "已注册" in exc.value.detail

    @pytest.mark.asyncio
    async def test_login_existing_email(self, db):
        """login 类型，邮箱存在 → 成功."""
        mock_user = MagicMock(spec=User)
        db.query.return_value.filter.return_value.first.return_value = mock_user
        req = EmailSendCodeRequest(email="user@test.com", type="login")

        with patch("app.services.user_service.EmailService.send_verification_code", new=AsyncMock()):
            result = await UserService.send_email_code(db, req)
        assert result["expire_in"] == 300

    @pytest.mark.asyncio
    async def test_login_email_not_found(self, db):
        """login 类型，邮箱不存在 → 404."""
        db.query.return_value.filter.return_value.first.return_value = None
        req = EmailSendCodeRequest(email="nonexistent@test.com", type="login")

        with pytest.raises(HTTPException) as exc:
            await UserService.send_email_code(db, req)
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_dev_code_returned_when_smtp_not_configured(self, db):
        """smtp_configured=False → 返回 dev_code."""
        db.query.return_value.filter.return_value.first.return_value = None
        req = EmailSendCodeRequest(email="dev@test.com", type="register")

        with patch("app.services.user_service.EmailService.send_verification_code", new=AsyncMock()):
            result = await UserService.send_email_code(db, req)
        assert "dev_code" in result
        assert len(result["dev_code"]) == 6

    @pytest.mark.asyncio
    async def test_email_send_failure_returns_502(self, db):
        """邮件发送失败（SMTP 异常）→ 502."""
        db.query.return_value.filter.return_value.first.return_value = None
        req = EmailSendCodeRequest(email="fail@test.com", type="register")

        from app.services.email_service import EmailSendError
        with patch(
            "app.services.user_service.EmailService.send_verification_code",
            new=AsyncMock(side_effect=EmailSendError("SMTP connection failed")),
        ):
            with pytest.raises(HTTPException) as exc:
                await UserService.send_email_code(db, req)
            assert exc.value.status_code == 502


class TestVerifyEmailCode:
    """Tests for UserService.verify_email_code()."""

    def test_verify_success(self, mocker):
        """验证码正确 → verified=True，设置 verified 标记."""
        mocker.patch("time.time", return_value=1000.0)
        VerificationCodeStore.set("email:register:test@test.com", "123456")
        # Override smtp_configured for the store behavior
        result = UserService.verify_email_code("test@test.com", "123456")
        assert result["verified"] is True
        # Original code deleted
        assert VerificationCodeStore.get("email:register:test@test.com") is None
        # Verified marker set
        assert VerificationCodeStore.get("email:verified:test@test.com") == "1"

    def test_wrong_code_returns_401(self):
        """错误验证码 → 401."""
        VerificationCodeStore.set("email:register:wrong@test.com", "111111")
        with pytest.raises(HTTPException) as exc:
            UserService.verify_email_code("wrong@test.com", "999999")
        assert exc.value.status_code == 401

    def test_missing_code_returns_401(self):
        """验证码不存在 → 401."""
        VerificationCodeStore.delete("email:register:missing@test.com")
        with pytest.raises(HTTPException) as exc:
            UserService.verify_email_code("missing@test.com", "000000")
        assert exc.value.status_code == 401

    def test_email_case_insensitive(self, mocker):
        """邮箱大小写不敏感."""
        mocker.patch("time.time", return_value=1000.0)
        VerificationCodeStore.set("email:register:test@test.com", "654321")
        result = UserService.verify_email_code("TEST@TEST.COM", "654321")
        assert result["verified"] is True


class TestRegisterByEmail:
    """Tests for UserService.register_by_email()."""

    MOCK_PROFILE = {
        "id": 1, "nickname": "test_user", "avatar_url": None, "bio": None,
        "phone": "", "email": "test@test.com", "role": "user",
        "auth_level": "basic", "is_professional": False,
        "risk_level": None, "investment_tags": None, "follow_markets": None,
        "achievements": {"posts_count": 0, "elite_posts": 0, "influence_score": 0, "badges": []},
        "points": 0, "level": 1, "privacy_settings": None, "created_at": None,
    }

    def _setup(self, db, verified=True):
        """Common setup for register_by_email tests."""
        if verified:
            VerificationCodeStore.set("email:verified:test@test.com", "1", ttl_seconds=600)
        # No duplicate
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        db.query.return_value = mock_q
        mock_q.first.return_value = None

    def test_normal_register_by_email(self, db, mocker):
        """正常邮箱注册 → 返回完整响应."""
        mocker.patch("time.time", return_value=1000.0)
        self._setup(db)
        req = EmailRegisterRequest(email="test@test.com", password="TestPass123", nickname="test_user")

        with patch(
            "app.services.user_service.UserService._build_profile",
            return_value=self.MOCK_PROFILE,
        ), patch("app.services.user_service.get_password_hash") as mock_gph, \
             patch("app.services.user_service.create_access_token") as mock_cat, \
             patch("app.services.user_service.create_refresh_token_record") as mock_crtr, \
             patch("app.services.user_service.datetime") as mock_dt:
            mock_gph.return_value = "hashed"
            mock_cat.return_value = "email_access_token"
            mock_crtr.return_value = ("raw_rt", "hash_rt", mock_dt.now())

            result = UserService.register_by_email(db, req)

        assert result["token"] == "email_access_token"
        assert result["refresh_token"] == "raw_rt"
        assert result["expires_in"] == 7200
        assert result["user"] == self.MOCK_PROFILE
        # Verified marker should be cleaned up
        assert VerificationCodeStore.get("email:verified:test@test.com") is None

    def test_unverified_email_returns_400(self, db):
        """未验证邮箱 → 400."""
        self._setup(db, verified=False)
        req = EmailRegisterRequest(email="test@test.com", password="TestPass123")
        with pytest.raises(HTTPException) as exc:
            UserService.register_by_email(db, req)
        assert exc.value.status_code == 400
        assert "验证" in exc.value.detail

    def test_duplicate_email_returns_409(self, db, mocker):
        """重复邮箱 → 409."""
        mocker.patch("time.time", return_value=1000.0)
        self._setup(db)
        # Duplicate user found
        mock_user = MagicMock(spec=User)
        db.query.return_value.filter.return_value.first.return_value = mock_user

        req = EmailRegisterRequest(email="test@test.com", password="TestPass123")
        with pytest.raises(HTTPException) as exc:
            UserService.register_by_email(db, req)
        assert exc.value.status_code == 409
        assert "已注册" in exc.value.detail

    def test_auto_generate_nickname_from_email(self, db, mocker):
        """无昵称 → 从邮箱本地部分自动生成."""
        mocker.patch("time.time", return_value=1000.0)
        VerificationCodeStore.set("email:verified:hello@test.com", "1", ttl_seconds=600)
        # No duplicate
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        db.query.return_value = mock_q
        mock_q.first.return_value = None

        req = EmailRegisterRequest(email="hello@test.com", password="TestPass123")

        with patch(
            "app.services.user_service.UserService._build_profile",
            return_value=self.MOCK_PROFILE,
        ), patch("app.services.user_service.get_password_hash") as mock_gph, \
             patch("app.services.user_service.create_access_token") as mock_cat, \
             patch("app.services.user_service.create_refresh_token_record") as mock_crtr:
            mock_gph.return_value = "hashed"
            mock_cat.return_value = "token"
            mock_crtr.return_value = ("raw", "hash", MagicMock())

            result = UserService.register_by_email(db, req)

        # Verify the user was created with correct attributes
        db.add.assert_called()
        user_arg = db.add.call_args_list[0][0][0]
        assert user_arg.nickname.startswith("用户")
        assert user_arg.register_type == RegisterType.EMAIL
        assert user_arg.auth_level == AuthLevel.BASIC
