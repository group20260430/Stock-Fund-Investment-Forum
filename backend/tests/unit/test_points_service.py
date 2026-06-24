"""Unit tests for PointsService — get_level() and award_points()."""

from unittest.mock import MagicMock

import pytest

from app.models.points import PointsHistory
from app.services.points_service import LEVEL_THRESHOLDS, award_points, get_level


class TestGetLevel:
    """Tests for get_level() — pure function, no DB."""

    @pytest.mark.parametrize(
        "points,expected_level",
        [
            # Level 1 boundaries
            (0, 1),
            (99, 1),
            # Level 2 boundaries
            (100, 2),
            (299, 2),
            # Level 3 boundaries
            (300, 3),
            (599, 3),
            # Level 4 boundaries
            (600, 4),
            (999, 4),
            # Level 5 boundaries
            (1000, 5),
            (1999, 5),
            # Level 6 boundaries
            (2000, 6),
            (4999, 6),
            # Level 7 boundaries
            (5000, 7),
            (9999, 7),
            # Level 8 boundaries
            (10000, 8),
            # Above max threshold
            (20000, 8),
        ],
    )
    def test_level_boundaries(self, points, expected_level):
        """验证所有等级边界值：0→L1, 99→L1, 100→L2, ..., 10000→L8."""
        assert get_level(points) == expected_level

    def test_negative_points_returns_level_1(self):
        """负积分 → 返回 L1（无更低等级）."""
        assert get_level(-100) == 1

    def test_level_thresholds_structure(self):
        """验证 LEVEL_THRESHOLDS 常量结构."""
        assert len(LEVEL_THRESHOLDS) == 7
        assert LEVEL_THRESHOLDS[0] == (100, 2)
        assert LEVEL_THRESHOLDS[-1] == (10000, 8)
        # Verify thresholds are in ascending order
        for i in range(1, len(LEVEL_THRESHOLDS)):
            assert LEVEL_THRESHOLDS[i][0] > LEVEL_THRESHOLDS[i - 1][0]


class TestAwardPoints:
    """Tests for award_points() — with mocked DB session."""

    # ── Event type parametrized tests ─────────────────────────────────────

    @pytest.mark.parametrize(
        "reason,points_change",
        [
            ("daily_login", 1),
            ("create_post", 5),
            ("create_comment", 2),
            ("post_liked", 1),
            ("comment_liked", 1),
            ("post_shared", 3),
            ("gained_follower", 1),
            ("delete_post", -5),
            ("delete_comment", -2),
            ("post_unliked", -1),
            ("comment_unliked", -1),
            ("lost_follower", -1),
        ],
    )
    def test_all_event_types(self, db, reason, points_change):
        """所有积分事件类型测试：验证每种事件正确加减分."""
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.points = 100

        db.query.return_value.filter.return_value.first.return_value = mock_user

        award_points(db, user_id=1, points=points_change, reason=reason)

        assert mock_user.points == 100 + points_change
        # Verify update_level was set after points recalculation
        assert mock_user.level is not None

    # ── User not found ────────────────────────────────────────────────────

    def test_user_not_found_silently_ignored(self, db):
        """用户不存在时 award_points 静默忽略，不操作."""
        db.query.return_value.filter.return_value.first.return_value = None

        # Should not raise
        award_points(db, user_id=999, points=10, reason="daily_login")

        # No points changed, no PointsHistory created
        db.add.assert_not_called()

    # ── Level downgrade ───────────────────────────────────────────────────

    def test_level_downgrade_on_negative_points(self, db):
        """积分扣减后低于阈值 → 等级自动降级（L2→L1）."""
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.points = 150  # Currently L2 (≥100)
        mock_user.level = 2

        db.query.return_value.filter.return_value.first.return_value = mock_user

        # Deduct 60 points → 90, below L2 threshold → should be L1
        award_points(db, user_id=1, points=-60, reason="delete_post")

        assert mock_user.points == 90
        assert mock_user.level == 1

    # ── PointsHistory creation ────────────────────────────────────────────

    def test_points_history_record_created(self, db):
        """验证 PointsHistory 记录的创建."""
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.points = 0
        mock_user.level = 1

        db.query.return_value.filter.return_value.first.return_value = mock_user

        award_points(db, user_id=1, points=5, reason="create_post")

        # Verify db.add was called with a PointsHistory instance
        db.add.assert_called_once()
        args = db.add.call_args[0]
        assert len(args) == 1
        # Should be a PointsHistory instance (real object, not mock)
        from app.models.points import PointsHistory
        assert isinstance(args[0], PointsHistory)
        assert args[0].user_id == 1
        assert args[0].points_change == 5
        assert args[0].reason == "create_post"

    # ── Reference fields ──────────────────────────────────────────────────

    def test_reference_fields_passed_through(self, db):
        """验证 reference_type 和 reference_id 正确传递."""
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.points = 0
        mock_user.level = 1

        db.query.return_value.filter.return_value.first.return_value = mock_user

        award_points(
            db,
            user_id=1,
            points=5,
            reason="create_post",
            reference_type="post",
            reference_id=42,
        )

        # Verify PointsHistory was added with correct reference fields
        db.add.assert_called_once()
        args = db.add.call_args[0]
        assert args[0].reference_type == "post"
        assert args[0].reference_id == 42

    def test_points_handle_none_initial_points(self, db):
        """初始积分为 None 时，当作 0 处理."""
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.points = None  # None
        mock_user.level = 1

        db.query.return_value.filter.return_value.first.return_value = mock_user

        award_points(db, user_id=1, points=10, reason="daily_login")

        assert mock_user.points == 10
