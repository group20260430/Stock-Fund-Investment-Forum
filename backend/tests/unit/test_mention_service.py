"""Unit tests for MentionService — @mention parsing and notification dispatch."""

from unittest.mock import MagicMock, patch

from app.models.notification import Notification, NotificationType
from app.models.user import User
from app.services.mention_service import (
    create_mention_notifications,
    parse_mentions,
    validate_mentions,
)


class TestParseMentions:
    """Tests for parse_mentions() — pure function, no DB."""

    def test_single_mention(self):
        """"@张三 来看看这个" → 解析出 ["张三"]."""
        result = parse_mentions("@张三 来看看这个")
        assert result == ["张三"]

    def test_multiple_mentions(self):
        """" @李四 @王五 两个" → 解析出两个用户名（需要@前有空格或开头）."""
        result = parse_mentions(" @李四 @王五 两个")
        # Result may be deduplicated in any order
        assert len(result) == 2
        assert "李四" in result
        assert "王五" in result

    def test_no_mention_returns_empty(self):
        """无 @提及 → 空列表."""
        result = parse_mentions("这是一段普通文本，没有提到任何人")
        assert result == []

    def test_at_alone_returns_empty(self):
        """"@" 单独 → 空列表（@后面无有效用户名）."""
        result = parse_mentions("@ 来看看")
        assert result == []

        result2 = parse_mentions("Just an @ sign")
        assert result2 == []

    def test_email_address_not_matched(self):
        """邮箱地址不应被匹配（@前面没有空白/开头）."""
        result = parse_mentions("Contact me at user@domain.com")
        assert "domain.com" not in result
        assert "user" not in result

    def test_chinese_username(self):
        """中文用户名匹配."""
        result = parse_mentions("@投资达人 说得对")
        assert "投资达人" in result

    def test_alphanumeric_username(self):
        """英文+数字+下划线用户名匹配."""
        result = parse_mentions("Hey @user_123 check this")
        assert "user_123" in result

    def test_deduplicate_mentions(self):
        """重复 @提及 → 去重."""
        result = parse_mentions("@张三 和 @张三 和 @李四")
        assert result == ["张三", "李四"] or set(result) == {"张三", "李四"}

    def test_empty_content_returns_empty(self):
        """空内容 → 空列表."""
        result = parse_mentions("")
        assert result == []

    def test_none_content_returns_empty(self):
        """None 内容 → 空列表."""
        result = parse_mentions(None)
        assert result == []

    def test_mention_at_end_of_text(self):
        """文本末尾的 @提及."""
        result = parse_mentions("Check this out @王五")
        assert "王五" in result

    def test_mention_followed_by_punctuation(self):
        """@提及后跟标点符号."""
        result = parse_mentions("@张三, @李四! 来看看")
        assert "张三" in result
        assert "李四" in result


class TestValidateMentions:
    """Tests for validate_mentions() — with mocked DB."""

    def test_existing_user_resolved(self, db):
        """已存在用户 → 解析为 user_id."""
        alice = MagicMock(spec=User)
        alice.nickname = "alice"
        alice.id = 42

        db.query.return_value.filter.return_value.all.return_value = [alice]

        result = validate_mentions(db, ["alice"])
        assert result == {"alice": 42}

    def test_nonexistent_user_ignored(self, db):
        """不存在的用户 → 静默忽略."""
        db.query.return_value.filter.return_value.all.return_value = []

        result = validate_mentions(db, ["nonexistent"])
        assert result == {}

    def test_empty_list_returns_empty(self, db):
        """空列表 → 空字典."""
        result = validate_mentions(db, [])
        assert result == {}
        # db.query should not be called
        db.query.assert_not_called()

    def test_multiple_users_mixed(self, db):
        """混合存在/不存在的用户."""
        alice = MagicMock(spec=User)
        alice.nickname = "alice"
        alice.id = 1
        bob = MagicMock(spec=User)
        bob.nickname = "bob"
        bob.id = 2

        db.query.return_value.filter.return_value.all.return_value = [alice, bob]

        result = validate_mentions(db, ["alice", "bob", "charlie"])
        assert result == {"alice": 1, "bob": 2}


class TestCreateMentionNotifications:
    """Tests for create_mention_notifications() — with mocked DB."""

    def test_create_notification_called(self, db):
        """正常 @提及 → 创建通知."""
        with patch("app.services.mention_service.create_notification") as mock_cn:
            # No existing duplicate notification
            db.query.return_value.filter.return_value.first.return_value = None

            create_mention_notifications(
                db,
                mentioned_user_ids=[2],
                sender_id=1,
                source_type="post",
                source_id=42,
            )

            assert mock_cn.call_count == 1
            # Verify call args
            call_kwargs = mock_cn.call_args[1] if mock_cn.call_args.kwargs else {}
            positional_args = mock_cn.call_args[0]
            # create_notification(db, uid, type, title, content, target_type, target_id, sender_id)
            assert positional_args[1] == 2  # user_id
            assert positional_args[2] == NotificationType.MENTION

    def test_self_mention_skipped(self, db):
        """@自己 → 不创建通知."""
        with patch("app.services.mention_service.create_notification") as mock_cn:
            db.query.return_value.filter.return_value.first.return_value = None

            create_mention_notifications(
                db,
                mentioned_user_ids=[1],  # same as sender
                sender_id=1,
                source_type="post",
                source_id=42,
            )

            mock_cn.assert_not_called()

    def test_duplicate_notification_skipped(self, db):
        """已存在的通知 → 跳过，不重复创建."""
        with patch("app.services.mention_service.create_notification") as mock_cn:
            # Existing notification found
            db.query.return_value.filter.return_value.first.return_value = MagicMock()

            create_mention_notifications(
                db,
                mentioned_user_ids=[2],
                sender_id=1,
                source_type="post",
                source_id=42,
            )

            mock_cn.assert_not_called()

    def test_multiple_recipients(self, db):
        """多个 @提及 → 每个被提及用户都收到通知."""
        with patch("app.services.mention_service.create_notification") as mock_cn:
            # No existing duplicate notifications
            db.query.return_value.filter.return_value.first.return_value = None

            create_mention_notifications(
                db,
                mentioned_user_ids=[2, 3, 4],
                sender_id=1,
                source_type="post",
                source_id=42,
            )

            assert mock_cn.call_count == 3

    def test_skip_self_in_mixed_list(self, db):
        """混合列表包含自己 → 跳过自己但通知他人."""
        with patch("app.services.mention_service.create_notification") as mock_cn:
            db.query.return_value.filter.return_value.first.return_value = None

            create_mention_notifications(
                db,
                mentioned_user_ids=[1, 2, 3],  # 1 is sender
                sender_id=1,
                source_type="post",
                source_id=42,
            )

            assert mock_cn.call_count == 2  # only 2 and 3
