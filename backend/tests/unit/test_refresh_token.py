"""Unit tests for UserService.refresh_token() — Token refresh with rotation."""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.models.refresh_token import RefreshToken
from app.models.user import User, UserStatus
from app.services.user_service import UserService


class TestRefreshToken:
    """Tests for UserService.refresh_token()."""

    # ── Normal refresh ────────────────────────────────────────────────────

    def test_normal_refresh_returns_new_token_pair(self, db):
        """正常刷新 → 返回新 access_token + refresh_token, 旧 Token 被吊销."""
        raw_token = "old_raw_refresh_token_64chars"
        mock_stored = MagicMock(spec=RefreshToken)
        mock_stored.user_id = 1
        mock_stored.is_revoked = False
        mock_stored.expires_at = datetime.now(timezone.utc) + timedelta(days=3)

        mock_user = MagicMock(spec=User)
        mock_user.id = 1
        mock_user.status = UserStatus.ACTIVE

        # Set up db.query side_effect: first query for RefreshToken, second for User
        mock_q1 = MagicMock()
        mock_q1.filter.return_value = mock_q1
        mock_q1.first.return_value = mock_stored

        mock_q2 = MagicMock()
        mock_q2.filter.return_value = mock_q2
        mock_q2.first.return_value = mock_user

        db.query.side_effect = [mock_q1, mock_q2]

        with patch(
            "app.services.user_service.hash_refresh_token"
        ) as mock_hash, patch(
            "app.services.user_service.create_access_token"
        ) as mock_cat, patch(
            "app.services.user_service.create_refresh_token_record"
        ) as mock_crtr:
            mock_hash.return_value = "sha256_hash_of_old_token"
            mock_cat.return_value = "new_access_token_after_refresh"
            mock_crtr.return_value = (
                "new_raw_refresh_token",
                "new_token_hash",
                datetime.now(timezone.utc) + timedelta(days=7),
            )

            result = UserService.refresh_token(raw_token, db)

        assert result["token"] == "new_access_token_after_refresh"
        assert result["refresh_token"] == "new_raw_refresh_token"
        assert result["expires_in"] == 7200
        # Old token should be revoked
        assert mock_stored.is_revoked is True

    # ── Token not found ───────────────────────────────────────────────────

    def test_token_not_found_raises_401(self, db):
        """Token 不存在于数据库 → 401."""
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        db.query.return_value = mock_q
        mock_q.first.return_value = None  # token not found

        with patch(
            "app.services.user_service.hash_refresh_token"
        ) as mock_hash:
            mock_hash.return_value = "nonexistent_hash"

            with pytest.raises(HTTPException) as exc_info:
                UserService.refresh_token("bad_token", db)
            assert exc_info.value.status_code == 401

    # ── Revoked token ─────────────────────────────────────────────────────

    def test_revoked_token_raises_401(self, db):
        """使用已吊销 Token → 401（同时触发全族吊销）."""
        mock_stored = MagicMock(spec=RefreshToken)
        mock_stored.user_id = 1
        mock_stored.is_revoked = True
        mock_stored.expires_at = datetime.now(timezone.utc) + timedelta(days=3)

        # First query: lookup token → returns revoked token
        mock_q1 = MagicMock()
        mock_q1.filter.return_value = mock_q1
        mock_q1.first.return_value = mock_stored

        # Second query: bulk revocation (db.query(RefreshToken).filter(...).update(...))
        mock_q2 = MagicMock()
        mock_q2.filter.return_value = mock_q2

        db.query.side_effect = [mock_q1, mock_q2]

        with patch(
            "app.services.user_service.hash_refresh_token"
        ) as mock_hash:
            mock_hash.return_value = "revoked_token_hash"

            with pytest.raises(HTTPException) as exc_info:
                UserService.refresh_token("revoked_token", db)
            assert exc_info.value.status_code == 401

    # ── Expired token ─────────────────────────────────────────────────────

    def test_expired_token_raises_401(self, db):
        """使用过期 Token → 401."""
        mock_stored = MagicMock(spec=RefreshToken)
        mock_stored.user_id = 1
        mock_stored.is_revoked = False
        # Token expired 1 day ago
        mock_stored.expires_at = datetime.now(timezone.utc) - timedelta(days=1)

        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        db.query.return_value = mock_q
        mock_q.first.return_value = mock_stored

        with patch(
            "app.services.user_service.hash_refresh_token"
        ) as mock_hash:
            mock_hash.return_value = "expired_token_hash"

            with pytest.raises(HTTPException) as exc_info:
                UserService.refresh_token("expired_token", db)
            assert exc_info.value.status_code == 401

    # ── Hash mismatch / token not found ───────────────────────────────────

    def test_hash_mismatch_raises_401(self, db):
        """hash 比对失败（被篡改）→ 401."""
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        db.query.return_value = mock_q
        mock_q.first.return_value = None  # no matching hash

        with patch(
            "app.services.user_service.hash_refresh_token"
        ) as mock_hash:
            mock_hash.return_value = "tampered_hash"

            with pytest.raises(HTTPException) as exc_info:
                UserService.refresh_token("tampered_token", db)
            assert exc_info.value.status_code == 401

    # ── User disabled after token issuance ────────────────────────────────

    def test_user_disabled_raises_401(self, db):
        """Token 有效但用户已被禁用 → 401."""
        mock_stored = MagicMock(spec=RefreshToken)
        mock_stored.user_id = 1
        mock_stored.is_revoked = False
        mock_stored.expires_at = datetime.now(timezone.utc) + timedelta(days=3)

        mock_user_disabled = MagicMock(spec=User)
        mock_user_disabled.id = 1
        mock_user_disabled.status = UserStatus.DISABLED

        mock_q1 = MagicMock()
        mock_q1.filter.return_value = mock_q1
        mock_q1.first.return_value = mock_stored

        mock_q2 = MagicMock()
        mock_q2.filter.return_value = mock_q2
        mock_q2.first.return_value = mock_user_disabled

        db.query.side_effect = [mock_q1, mock_q2]

        with patch(
            "app.services.user_service.hash_refresh_token"
        ) as mock_hash:
            mock_hash.return_value = "valid_token_hash"
            with pytest.raises(HTTPException) as exc_info:
                UserService.refresh_token("valid_raw_token", db)
            assert exc_info.value.status_code == 401

    # ── User not found after token issuance ───────────────────────────────

    def test_user_not_found_raises_401(self, db):
        """Token 有效但用户已被删除 → 401."""
        mock_stored = MagicMock(spec=RefreshToken)
        mock_stored.user_id = 999
        mock_stored.is_revoked = False
        mock_stored.expires_at = datetime.now(timezone.utc) + timedelta(days=3)

        mock_q1 = MagicMock()
        mock_q1.filter.return_value = mock_q1
        mock_q1.first.return_value = mock_stored

        mock_q2 = MagicMock()
        mock_q2.filter.return_value = mock_q2
        mock_q2.first.return_value = None  # user not found

        db.query.side_effect = [mock_q1, mock_q2]

        with patch(
            "app.services.user_service.hash_refresh_token"
        ) as mock_hash:
            mock_hash.return_value = "orphan_token_hash"
            with pytest.raises(HTTPException) as exc_info:
                UserService.refresh_token("orphan_token", db)
            assert exc_info.value.status_code == 401
