"""Unit tests for UserService.login() — login method."""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.models.user import UserStatus
from app.schemas.user import LoginRequest
from app.services.user_service import UserService, VerificationCodeStore


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


class TestUserServiceLogin:
    """Tests for UserService.login()."""

    # ── Password login ────────────────────────────────────────────────────

    def test_password_login_success(self, db, mock_user):
        """正确手机号+密码 → 200，返回 token + user profile."""
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        db.query.return_value = mock_q
        mock_q.first.return_value = mock_user

        with patch(
            "app.services.user_service.UserService._build_profile",
            return_value=MOCK_PROFILE,
        ), patch(
            "app.services.user_service.verify_password", return_value=True
        ), patch(
            "app.services.user_service.record_activity"
        ), patch(
            "app.services.user_service.award_points"
        ), patch(
            "app.services.user_service.create_access_token"
        ) as mock_cat, patch(
            "app.services.user_service.create_refresh_token_record"
        ) as mock_crtr:
            mock_cat.return_value = "access_token_login"
            mock_crtr.return_value = (
                "raw_rt_login",
                "hash_login",
                datetime.now(timezone.utc) + timedelta(days=7),
            )

            req = LoginRequest(
                phone="13800138000",
                password="TestPass123",
                login_type="password",
            )
            result = UserService.login(db, req)

        assert result["user_id"] == 1
        assert result["token"] == "access_token_login"
        assert result["expires_in"] == 7200
        assert result["user"] == MOCK_PROFILE

    # ── Code login ────────────────────────────────────────────────────────

    def test_code_login_success(self, db, mock_user, mocker):
        """正确手机号+验证码 → 200."""
        mocker.patch("time.time", return_value=1000.0)
        VerificationCodeStore.set("login:13800138000", "654321")

        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        db.query.return_value = mock_q
        mock_q.first.return_value = mock_user

        with patch(
            "app.services.user_service.UserService._build_profile",
            return_value=MOCK_PROFILE,
        ), patch(
            "app.services.user_service.record_activity"
        ), patch(
            "app.services.user_service.award_points"
        ), patch(
            "app.services.user_service.create_access_token"
        ) as mock_cat, patch(
            "app.services.user_service.create_refresh_token_record"
        ) as mock_crtr:
            mock_cat.return_value = "access_token_code"
            mock_crtr.return_value = (
                "raw_rt_code",
                "hash_code",
                datetime.now(timezone.utc) + timedelta(days=7),
            )

            req = LoginRequest(
                phone="13800138000",
                code="654321",
                login_type="code",
            )
            result = UserService.login(db, req)

        assert result["token"] == "access_token_code"

    # ── Wrong password ────────────────────────────────────────────────────

    def test_wrong_password_raises_401(self, db, mock_user):
        """错误密码 → 401."""
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        db.query.return_value = mock_q
        mock_q.first.return_value = mock_user

        with patch(
            "app.services.user_service.verify_password", return_value=False
        ):
            req = LoginRequest(
                phone="13800138000",
                password="WrongPassword1",
                login_type="password",
            )
            with pytest.raises(HTTPException) as exc_info:
                UserService.login(db, req)
            assert exc_info.value.status_code == 401

    # ── Wrong code ────────────────────────────────────────────────────────

    def test_wrong_code_raises_401(self, db, mock_user, mocker):
        """错误验证码 → 401."""
        mocker.patch("time.time", return_value=1000.0)
        VerificationCodeStore.set("login:13800138000", "111111")

        req = LoginRequest(
            phone="13800138000",
            code="999999",  # wrong code
            login_type="code",
        )
        with pytest.raises(HTTPException) as exc_info:
            UserService.login(db, req)
        assert exc_info.value.status_code == 401

    # ── User not found (code login) ───────────────────────────────────────

    def test_user_not_found_code_login_raises_404(self, db, mocker):
        """未注册手机号 → 404（验证码正确但用户不存在）."""
        mocker.patch("time.time", return_value=1000.0)
        VerificationCodeStore.set("login:13800138001", "123456")

        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        db.query.return_value = mock_q
        mock_q.first.return_value = None

        req = LoginRequest(
            phone="13800138001",
            code="123456",
            login_type="code",
        )
        with pytest.raises(HTTPException) as exc_info:
            UserService.login(db, req)
        assert exc_info.value.status_code == 404

    # ── Disabled user ─────────────────────────────────────────────────────

    def test_disabled_user_raises_401(self, db, mock_user):
        """用户已封禁（DISABLED）→ 401."""
        mock_user.status = UserStatus.DISABLED

        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        db.query.return_value = mock_q
        mock_q.first.return_value = mock_user

        with patch(
            "app.services.user_service.verify_password", return_value=True
        ):
            req = LoginRequest(
                phone="13800138000",
                password="TestPass123",
                login_type="password",
            )
            with pytest.raises(HTTPException) as exc_info:
                UserService.login(db, req)
            assert exc_info.value.status_code == 401
            assert "禁用" in exc_info.value.detail

    # ── Daily login points ────────────────────────────────────────────────

    def test_daily_login_points_awarded(self, db, mock_user):
        """当日首次登录 → 验证 award_points 被调用."""
        # Three db.query calls: user lookup, PointsHistory check, award_points user lookup
        mock_q1 = MagicMock()
        mock_q1.filter.return_value = mock_q1
        mock_q1.first.return_value = mock_user

        mock_q2 = MagicMock()
        mock_q2.filter.return_value = mock_q2
        mock_q2.first.return_value = None  # No daily record yet

        # award_points also calls db.query
        mock_q3 = MagicMock()
        mock_q3.filter.return_value = mock_q3
        mock_q3.first.return_value = mock_user

        db.query.side_effect = [mock_q1, mock_q2, mock_q3]

        with patch(
            "app.services.user_service.UserService._build_profile",
            return_value=MOCK_PROFILE,
        ), patch(
            "app.services.user_service.verify_password", return_value=True
        ), patch(
            "app.services.user_service.record_activity"
        ), patch(
            "app.services.user_service.award_points"
        ) as mock_ap, patch(
            "app.services.user_service.create_access_token"
        ) as mock_cat, patch(
            "app.services.user_service.create_refresh_token_record"
        ) as mock_crtr:
            mock_cat.return_value = "access_token"
            mock_crtr.return_value = (
                "raw_rt",
                "hash",
                datetime.now(timezone.utc) + timedelta(days=7),
            )

            req = LoginRequest(
                phone="13800138000",
                password="TestPass123",
                login_type="password",
            )
            UserService.login(db, req)

        # award_points should be called with 1 point for daily_login
        mock_ap.assert_called_once()
        call_args = mock_ap.call_args[0]
        assert call_args[2] == 1  # points
        assert call_args[3] == "daily_login"  # reason

    # ── Repeat login no points ────────────────────────────────────────────

    def test_repeat_login_same_day_no_points(self, db, mock_user):
        """同一天再次登录 → 验证 award_points 不被调用."""
        mock_q1 = MagicMock()
        mock_q1.filter.return_value = mock_q1
        mock_q1.first.return_value = mock_user

        mock_q2 = MagicMock()
        mock_q2.filter.return_value = mock_q2
        # PointsHistory record found (already awarded today)
        mock_q2.first.return_value = MagicMock()

        # award_points also calls db.query, but shouldn't be reached
        mock_q3 = MagicMock()
        mock_q3.filter.return_value = mock_q3
        mock_q3.first.return_value = mock_user

        db.query.side_effect = [mock_q1, mock_q2, mock_q3]

        with patch(
            "app.services.user_service.UserService._build_profile",
            return_value=MOCK_PROFILE,
        ), patch(
            "app.services.user_service.verify_password", return_value=True
        ), patch(
            "app.services.user_service.record_activity"
        ), patch(
            "app.services.user_service.award_points"
        ) as mock_ap, patch(
            "app.services.user_service.create_access_token"
        ) as mock_cat, patch(
            "app.services.user_service.create_refresh_token_record"
        ) as mock_crtr:
            mock_cat.return_value = "access_token"
            mock_crtr.return_value = (
                "raw_rt",
                "hash",
                datetime.now(timezone.utc) + timedelta(days=7),
            )

            req = LoginRequest(
                phone="13800138000",
                password="TestPass123",
                login_type="password",
            )
            UserService.login(db, req)

        # award_points should NOT be called (already awarded today)
        mock_ap.assert_not_called()
