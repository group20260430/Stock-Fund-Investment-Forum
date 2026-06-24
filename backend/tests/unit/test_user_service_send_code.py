"""Unit tests for UserService.send_code / verify_code / reset_password."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.models.user import User
from app.schemas.user import ResetPasswordRequest, SendCodeRequest
from app.services.user_service import UserService, VerificationCodeStore


class TestSendCode:
    """Tests for UserService.send_code()."""

    # ── Register type ─────────────────────────────────────────────────────

    def test_send_code_register_new_user(self, db):
        """register 类型，用户不存在 → 成功."""
        db.query.return_value.filter.return_value.first.return_value = None
        req = SendCodeRequest(phone="13800138001", type="register")

        result = UserService.send_code(db, req)
        assert result["expire_in"] == 300

    def test_send_code_register_duplicate(self, db):
        """register 类型，用户已存在 → 409."""
        mock_user = MagicMock(spec=User)
        db.query.return_value.filter.return_value.first.return_value = mock_user
        req = SendCodeRequest(phone="13800138000", type="register")

        with pytest.raises(HTTPException) as exc_info:
            UserService.send_code(db, req)
        assert exc_info.value.status_code == 409
        assert "已注册" in exc_info.value.detail

    # ── Login type ────────────────────────────────────────────────────────

    def test_send_code_login_existing_user(self, db):
        """login 类型，用户存在 → 成功."""
        mock_user = MagicMock(spec=User)
        db.query.return_value.filter.return_value.first.return_value = mock_user
        req = SendCodeRequest(phone="13800138000", type="login")

        result = UserService.send_code(db, req)
        assert result["expire_in"] == 300

    def test_send_code_login_user_not_found(self, db):
        """login 类型，用户不存在 → 404."""
        db.query.return_value.filter.return_value.first.return_value = None
        req = SendCodeRequest(phone="13800138001", type="login")

        with pytest.raises(HTTPException) as exc_info:
            UserService.send_code(db, req)
        assert exc_info.value.status_code == 404

    # ── Reset password type ───────────────────────────────────────────────

    def test_send_code_reset_password_existing_user(self, db):
        """reset_password 类型，用户存在 → 成功."""
        mock_user = MagicMock(spec=User)
        db.query.return_value.filter.return_value.first.return_value = mock_user
        req = SendCodeRequest(phone="13800138000", type="reset_password")

        result = UserService.send_code(db, req)
        assert result["expire_in"] == 300

    def test_send_code_reset_password_user_not_found(self, db):
        """reset_password 类型，用户不存在 → 404."""
        db.query.return_value.filter.return_value.first.return_value = None
        req = SendCodeRequest(phone="13800138001", type="reset_password")

        with pytest.raises(HTTPException) as exc_info:
            UserService.send_code(db, req)
        assert exc_info.value.status_code == 404

    # ── Dev code ──────────────────────────────────────────────────────────

    def test_dev_code_returned_when_smtp_not_configured(self, db):
        """smtp_configured=False 时 → 返回 dev_code."""
        db.query.return_value.filter.return_value.first.return_value = None
        req = SendCodeRequest(phone="13800138001", type="register")

        result = UserService.send_code(db, req)
        assert "dev_code" in result
        assert len(result["dev_code"]) == 6


class TestVerifyCode:
    """Tests for UserService.verify_code()."""

    def test_verify_code_wrong_code(self):
        """验证码不匹配 → 401."""
        VerificationCodeStore.set("register:13800138000", "123456")
        with pytest.raises(HTTPException) as exc_info:
            UserService.verify_code("13800138000", "654321", "register")
        assert exc_info.value.status_code == 401

    def test_verify_code_missing_code(self):
        """验证码不存在（已过期或未发送）→ 401."""
        # Ensure no code exists
        VerificationCodeStore.delete("register:13800138000")
        with pytest.raises(HTTPException) as exc_info:
            UserService.verify_code("13800138000", "000000", "register")
        assert exc_info.value.status_code == 401

    def test_verify_code_success(self, mocker):
        """验证码正确 → 返回 {"verified": True}，设置 verified 标记."""
        mocker.patch("time.time", return_value=1000.0)
        VerificationCodeStore.set("login:13800138000", "123456")

        result = UserService.verify_code("13800138000", "123456", "login")
        assert result["verified"] is True
        # Original code should be deleted
        assert VerificationCodeStore.get("login:13800138000") is None
        # Verified marker should be set
        assert VerificationCodeStore.get("verified:login:13800138000") == "1"


class TestResetPassword:
    """Tests for UserService.reset_password()."""

    def test_reset_password_missing_verification(self, db):
        """verified 标记不存在 → 400."""
        req = ResetPasswordRequest(
            phone="13800138000", code="123456", password="NewPass123"
        )
        with pytest.raises(HTTPException) as exc_info:
            UserService.reset_password(db, req)
        assert exc_info.value.status_code == 400
        assert "验证" in exc_info.value.detail

    def test_reset_password_user_not_found(self, db, mocker):
        """用户不存在 → 404."""
        mocker.patch("time.time", return_value=1000.0)
        # Set verified marker
        VerificationCodeStore.set(
            "verified:reset_password:13800138000", "1", ttl_seconds=600
        )
        # User not found
        db.query.return_value.filter.return_value.first.return_value = None

        req = ResetPasswordRequest(
            phone="13800138000", code="123456", password="NewPass123"
        )
        with pytest.raises(HTTPException) as exc_info:
            UserService.reset_password(db, req)
        assert exc_info.value.status_code == 404

    def test_reset_password_success(self, db, mocker):
        """正常重置密码 → 返回 {"success": True}."""
        mocker.patch("time.time", return_value=1000.0)
        # Set verified marker
        VerificationCodeStore.set(
            "verified:reset_password:13800138000", "1", ttl_seconds=600
        )
        mock_user = MagicMock(spec=User)
        mock_user.phone = "13800138000"
        db.query.return_value.filter.return_value.first.return_value = mock_user

        with patch(
            "app.services.user_service.get_password_hash"
        ) as mock_gph:
            mock_gph.return_value = "$2b$12$newhashedpassword"
            req = ResetPasswordRequest(
                phone="13800138000", code="123456", password="NewPass123"
            )
            result = UserService.reset_password(db, req)

        assert result["success"] is True
        mock_gph.assert_called_once_with("NewPass123")
        assert mock_user.password_hash == "$2b$12$newhashedpassword"
        db.commit.assert_called_once()
