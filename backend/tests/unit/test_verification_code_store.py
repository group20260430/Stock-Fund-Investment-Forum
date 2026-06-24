"""Unit tests for VerificationCodeStore — in-memory verification code store with TTL."""

import pytest

from app.services.user_service import VerificationCodeStore


class TestVerificationCodeStore:
    """Tests for VerificationCodeStore class methods."""

    # ── set + get ────────────────────────────────────────────────────────

    def test_set_and_get_normal(self, mocker):
        """存入后立即获取 → 返回正确 code."""
        mocker.patch("time.time", return_value=1000.0)
        VerificationCodeStore.set("register:13800138000", "123456", ttl_seconds=300)
        result = VerificationCodeStore.get("register:13800138000")
        assert result == "123456"

    # ── get expired ──────────────────────────────────────────────────────

    def test_get_expired_returns_none_and_deletes(self, mocker):
        """已过期的验证码 → 返回 None，条目被删除."""
        mocker.patch("time.time", return_value=1000.0)
        VerificationCodeStore.set("test:13800138000", "654321", ttl_seconds=60)
        # expire at 1060.0

        # Advance time past expiry
        mocker.patch("time.time", return_value=1060.1)
        result = VerificationCodeStore.get("test:13800138000")
        assert result is None
        # Verify entry was deleted
        assert "test:13800138000" not in VerificationCodeStore._codes

    def test_get_not_expired_at_exact_boundary(self, mocker):
        """刚好在过期时间点（未超过）→ 仍返回 code."""
        mocker.patch("time.time", return_value=1000.0)
        VerificationCodeStore.set("boundary:13800138000", "111111", ttl_seconds=60)
        # expires at 1060.0 exactly

        # At the exact boundary: time.time() == expires_at → not expired
        mocker.patch("time.time", return_value=1060.0)
        result = VerificationCodeStore.get("boundary:13800138000")
        assert result == "111111"

    # ── get non-existent ──────────────────────────────────────────────────

    def test_get_nonexistent_key_returns_none(self):
        """获取不存在的 key → 返回 None."""
        result = VerificationCodeStore.get("nonexistent:key")
        assert result is None

    # ── delete ───────────────────────────────────────────────────────────

    def test_delete_existing_key(self, mocker):
        """删除存在的 key → 之后 get 返回 None."""
        mocker.patch("time.time", return_value=1000.0)
        VerificationCodeStore.set("delete:13800138000", "222222", ttl_seconds=300)
        VerificationCodeStore.delete("delete:13800138000")
        assert VerificationCodeStore.get("delete:13800138000") is None

    def test_delete_nonexistent_key_no_error(self):
        """删除不存在的 key → 不抛异常（静默忽略）."""
        # Should not raise
        VerificationCodeStore.delete("nonexistent:key")
        # No exception means pass

    # ── cleanup_expired ──────────────────────────────────────────────────

    def test_cleanup_expired_mixed_states(self, mocker):
        """一个已过期一个未过期 → 删除 1 条，返回 1，剩余未过期的仍可取."""
        mocker.patch("time.time", return_value=1000.0)
        VerificationCodeStore.set("expired:13800138000", "aaa", ttl_seconds=60)
        VerificationCodeStore.set("valid:13800138001", "bbb", ttl_seconds=300)

        # Advance time past first entry's expiry but not second's
        mocker.patch("time.time", return_value=1100.0)
        removed = VerificationCodeStore.cleanup_expired()
        assert removed == 1
        # Expired entry should be gone
        assert "expired:13800138000" not in VerificationCodeStore._codes
        # Valid entry should still exist
        assert VerificationCodeStore.get("valid:13800138001") == "bbb"

    def test_cleanup_expired_empty_dict_returns_zero(self, mocker):
        """空 dict 时 cleanup_expired → 返回 0."""
        mocker.patch("time.time", return_value=1000.0)
        removed = VerificationCodeStore.cleanup_expired()
        assert removed == 0

    def test_cleanup_expired_all_valid_returns_zero(self, mocker):
        """所有条目都未过期 → 返回 0，不删除任何条目."""
        mocker.patch("time.time", return_value=1000.0)
        VerificationCodeStore.set("a:1", "x", ttl_seconds=300)
        VerificationCodeStore.set("b:2", "y", ttl_seconds=300)

        # Still within TTL
        mocker.patch("time.time", return_value=1100.0)
        removed = VerificationCodeStore.cleanup_expired()
        assert removed == 0
        assert VerificationCodeStore.get("a:1") == "x"
        assert VerificationCodeStore.get("b:2") == "y"

    # ── TTL precision ────────────────────────────────────────────────────

    def test_ttl_precision_set_with_300_seconds(self, mocker):
        """set 时 ttl_seconds=300 → expires_at = time.time() + 300."""
        mocker.patch("time.time", return_value=1000.0)
        VerificationCodeStore.set("ttl:13800138000", "999999", ttl_seconds=300)
        entry = VerificationCodeStore._codes["ttl:13800138000"]
        assert entry["expires_at"] == 1300.0
        assert entry["code"] == "999999"
