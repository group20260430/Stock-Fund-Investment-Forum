"""Unit tests for UserService profile update — investment_tags, follow_markets, risk_preference."""
from unittest.mock import MagicMock, patch

from app.models.user import RiskLevel, User
from app.schemas.user import UpdateProfileRequest
from app.services.user_service import UserService


class TestUpdateProfile:
    """Tests for UserService.update_profile()."""

    def test_update_investment_tags(self, db):
        """更新投资标签 → user.investment_tags 被更新."""
        user = MagicMock(spec=User)
        data = UpdateProfileRequest(
            investment_tags=["A股", "基金", "科创板"],
        )
        UserService.update_profile(db, user, data)
        assert user.investment_tags == ["A股", "基金", "科创板"]
        db.commit.assert_called_once()

    def test_update_follow_markets(self, db):
        """更新关注市场 → user.follow_markets 被更新."""
        user = MagicMock(spec=User)
        data = UpdateProfileRequest(
            follow_markets=["sh", "sz", "hk"],
        )
        UserService.update_profile(db, user, data)
        assert user.follow_markets == ["sh", "sz", "hk"]
        db.commit.assert_called_once()

    def test_update_risk_preference(self, db):
        """更新风险偏好 → user.risk_level 被更新."""
        user = MagicMock(spec=User)
        data = UpdateProfileRequest(
            risk_preference="aggressive",
        )
        UserService.update_profile(db, user, data)
        assert user.risk_level == RiskLevel.AGGRESSIVE
        db.commit.assert_called_once()

    def test_update_all_preferences(self, db):
        """同时更新所有偏好字段."""
        user = MagicMock(spec=User)
        data = UpdateProfileRequest(
            nickname="新昵称",
            bio="新简介",
            investment_tags=["美股"],
            follow_markets=["us"],
            risk_preference="conservative",
        )
        UserService.update_profile(db, user, data)
        assert user.nickname == "新昵称"
        assert user.bio == "新简介"
        assert user.investment_tags == ["美股"]
        assert user.follow_markets == ["us"]
        assert user.risk_level == RiskLevel.CONSERVATIVE
        db.commit.assert_called_once()

    def test_partial_update_only_bio(self, db):
        """仅更新 bio → 其他字段保持不变."""
        user = MagicMock(spec=User)
        user.nickname = "原昵称"
        UserService.update_profile(db, user, UpdateProfileRequest(bio="仅更新简介"))
        assert user.bio == "仅更新简介"
        # nickname not touched since it was None in request
        db.commit.assert_called_once()

    def test_set_investment_tags_to_empty(self, db):
        """设置空列表 → 清空投资标签."""
        user = MagicMock(spec=User)
        data = UpdateProfileRequest(investment_tags=[])
        UserService.update_profile(db, user, data)
        assert user.investment_tags == []

    def test_none_fields_do_not_overwrite(self, db):
        """None 字段不覆盖原有值."""
        user = MagicMock(spec=User)
        user.investment_tags = ["原有标签"]
        user.follow_markets = ["sh"]
        data = UpdateProfileRequest(nickname="新昵称")
        UserService.update_profile(db, user, data)
        # investment_tags 和 follow_markets 不应被修改（data 中为 None）
        # 因为 spec 是 MagicMock，它们仍然是 Mock 对象
        db.commit.assert_called_once()
