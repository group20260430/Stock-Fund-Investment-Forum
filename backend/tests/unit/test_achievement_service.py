"""Unit tests for AchievementService — badge calculation and influence scoring.

Strategy: mock db.query() to return a chain where scalar() uses side_effect
to return pre-defined values for each query call.  Since all queries follow
the pattern db.query(...).filter(...).scalar() or .all(), we share a single
mock query object whose scalar side_effect drives all return values.
"""
from unittest.mock import MagicMock

import pytest

from app.models.user import AuthLevel
from app.services.achievement_service import (
    BADGE_CERTIFIED,
    BADGE_COMMENTS_50,
    BADGE_ELITE_1,
    BADGE_ELITE_5,
    BADGE_FIRST_POST,
    BADGE_FOLLOWERS_10,
    BADGE_FOLLOWERS_50,
    BADGE_GROUP_ACTIVE,
    BADGE_GROUP_CREATOR,
    BADGE_LIKES_200,
    BADGE_LIKES_50,
    BADGE_10_POSTS,
    BADGE_50_POSTS,
    BADGE_100_POSTS,
    BADGE_PROFESSIONAL,
    BADGE_RISK_ASSESSED,
    BADGE_WARNED,
    calculate_achievements,
)


def _mock_user(**overrides):
    user = MagicMock()
    user.id = 1
    user.followers_count = 0
    user.risk_level = None
    user.auth_level = AuthLevel.NONE
    user.is_professional = False
    user.warn_count = 0
    for k, v in overrides.items():
        setattr(user, k, v)
    return user


class TestCalculateAchievements:
    """Tests for calculate_achievements()."""

    def _make_db(self, scalar_values, all_values=None):
        """
        Create a mock db Session.

        scalar_values: list of return values for sequential scalar() calls.
        all_values: list of return values for sequential all() calls (default []).
        """
        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.join.return_value = q
        q.scalar.side_effect = scalar_values
        q.all.side_effect = all_values or [[]] * len(scalar_values)
        db.query.return_value = q
        return db

    # ── New user ───────────────────────────────────────────────────

    def test_new_user_no_badges(self):
        """新用户无活动 → 空徽章，influence_score=0."""
        db = self._make_db([0, 0, 0, 0, 0, 0], [[], [], []])
        result = calculate_achievements(db, _mock_user())
        assert result.badges == []
        assert result.posts_count == 0
        assert result.influence_score == 0

    # ── Post milestones ───────────────────────────────────────────

    @pytest.mark.parametrize("posts,expected", [
        (0, []),
        (1, [BADGE_FIRST_POST[0]]),
        (10, [BADGE_FIRST_POST[0], BADGE_10_POSTS[0]]),
        (50, [BADGE_FIRST_POST[0], BADGE_10_POSTS[0], BADGE_50_POSTS[0]]),
        (100, [BADGE_FIRST_POST[0], BADGE_10_POSTS[0], BADGE_50_POSTS[0], BADGE_100_POSTS[0]]),
    ])
    def test_post_milestones(self, posts, expected):
        """发帖数达到阈值 → 解锁对应徽章."""
        db = self._make_db(
            [posts, 0, 0, 0, 0, 0],
            [[(i,) for i in range(posts)], [], []],
        )
        result = calculate_achievements(db, _mock_user())
        assert result.posts_count == posts
        for b in expected:
            assert b in result.badges

    # ── Elite posts ───────────────────────────────────────────────

    @pytest.mark.parametrize("elite,e1,e5", [(0, False, False), (1, True, False), (5, True, True)])
    def test_elite_badges(self, elite, e1, e5):
        """精华帖 ≥1 → 精华大师，≥5 → 精英作者."""
        # scalar calls: posts_count=5, elite_posts=elite, likes=0, comments=0, groups=0, msgs=0
        db = self._make_db([5, elite, 0, 0, 0, 0], [[(1,)], [], []])
        result = calculate_achievements(db, _mock_user())
        assert (BADGE_ELITE_1[0] in result.badges) == e1
        assert (BADGE_ELITE_5[0] in result.badges) == e5

    # ── Likes ─────────────────────────────────────────────────────

    @pytest.mark.parametrize("likes,exp50,exp200", [(0, False, False), (50, True, False), (200, True, True)])
    def test_likes_badges(self, likes, exp50, exp200):
        """获赞 ≥50 → 人气新星，≥200 → 万人迷."""
        db = self._make_db([1, 0, likes, 0, 0, 0], [[(1,)], [], []])
        result = calculate_achievements(db, _mock_user())
        assert (BADGE_LIKES_50[0] in result.badges) == exp50
        assert (BADGE_LIKES_200[0] in result.badges) == exp200

    # ── Followers ─────────────────────────────────────────────────

    @pytest.mark.parametrize("fans,exp10,exp50", [(0, False, False), (10, True, False), (50, True, True)])
    def test_followers_badges(self, fans, exp10, exp50):
        """粉丝 ≥10 → 社交达人，≥50 → 网红."""
        db = self._make_db([1, 0, 0, 0, 0, 0], [[(1,)], [], []])
        result = calculate_achievements(db, _mock_user(followers_count=fans))
        assert (BADGE_FOLLOWERS_10[0] in result.badges) == exp10
        assert (BADGE_FOLLOWERS_50[0] in result.badges) == exp50

    # ── Comments ──────────────────────────────────────────────────

    def test_comments_badge_given(self):
        """评论 ≥50 → 获得「评论家」."""
        db = self._make_db([1, 0, 0, 50, 0, 0], [[(1,)], [], []])
        assert BADGE_COMMENTS_50[0] in calculate_achievements(db, _mock_user()).badges

    def test_comments_badge_missing(self):
        """评论 <50 → 无徽章."""
        db = self._make_db([1, 0, 0, 10, 0, 0], [[(1,)], [], []])
        assert BADGE_COMMENTS_50[0] not in calculate_achievements(db, _mock_user()).badges

    # ── Risk ───────────────────────────────────────────────────────

    def test_risk_badge_given(self):
        """完成风险评估 → 获得「风险意识」."""
        db = self._make_db([0, 0, 0, 0, 0, 0], [[], [], []])
        assert BADGE_RISK_ASSESSED[0] in calculate_achievements(db, _mock_user(risk_level="moderate")).badges

    def test_risk_badge_missing(self):
        """未完成风险评估 → 无徽章."""
        db = self._make_db([0, 0, 0, 0, 0, 0], [[], [], []])
        assert BADGE_RISK_ASSESSED[0] not in calculate_achievements(db, _mock_user(risk_level=None)).badges

    # ── Certification ─────────────────────────────────────────────

    @pytest.mark.parametrize("al,is_pro,cert,pro", [
        (AuthLevel.NONE, False, False, False),
        (AuthLevel.BASIC, False, False, False),
        (AuthLevel.VERIFIED, False, True, False),
        (AuthLevel.PROFESSIONAL, False, True, True),
        (AuthLevel.VERIFIED, True, True, True),
    ])
    def test_certification_badges(self, al, is_pro, cert, pro):
        """实名认证 → 认证用户，专业认证(加V) → 专业人士."""
        db = self._make_db([0, 0, 0, 0, 0, 0], [[], [], []])
        result = calculate_achievements(db, _mock_user(auth_level=al, is_professional=is_pro))
        assert (BADGE_CERTIFIED[0] in result.badges) == cert
        assert (BADGE_PROFESSIONAL[0] in result.badges) == pro

    # ── Group ──────────────────────────────────────────────────────

    def test_group_creator_badge(self):
        """创建群组 → 获得「群组创建者」."""
        # scalar calls: posts=1, elite=0, likes=0, comments=0, groups=1, msgs=0
        # all calls: post_ids=[(1,)]
        db = self._make_db([1, 0, 0, 0, 1, 0], [[(1,)]])
        assert BADGE_GROUP_CREATOR[0] in calculate_achievements(db, _mock_user()).badges

    def test_group_active_badge(self):
        """群聊 ≥20 → 获得「社群活跃」."""
        # scalar: posts=1, elite=0, likes=0, comments=0, groups=0, msgs=20
        # all: post_ids=[(1,)]
        db = self._make_db([1, 0, 0, 0, 0, 20], [[(1,)]])
        assert BADGE_GROUP_ACTIVE[0] in calculate_achievements(db, _mock_user()).badges

    # ── Warn ───────────────────────────────────────────────────────

    def test_warned_badge(self):
        """收到过警告 → 获得「需留意」."""
        db = self._make_db([0, 0, 0, 0, 0, 0], [[], [], []])
        assert BADGE_WARNED[0] in calculate_achievements(db, _mock_user(warn_count=2)).badges

    def test_no_warn_no_badge(self):
        """未收到警告 → 无徽章."""
        db = self._make_db([0, 0, 0, 0, 0, 0], [[], [], []])
        assert BADGE_WARNED[0] not in calculate_achievements(db, _mock_user(warn_count=0)).badges

    # ── Influence score ───────────────────────────────────────────

    def test_influence_score(self):
        """影响力 = posts*10 + elite*50 + likes*2 + followers*5 + comments*3."""
        db = self._make_db(
            [3, 2, 10, 5, 0, 0],
            [[(1,), (2,), (3,)], [], []],
        )
        result = calculate_achievements(db, _mock_user(followers_count=8))
        assert result.influence_score == 3*10 + 2*50 + 10*2 + 8*5 + 5*3  # 205
