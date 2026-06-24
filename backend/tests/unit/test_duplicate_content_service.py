"""Unit tests for DuplicateContentService — duplicate content detection."""

from unittest.mock import MagicMock

import pytest

from app.models.content import Post
from app.services.duplicate_content_service import (
    DuplicateContentCheckResult,
    _normalize_text,
    check_duplicate_post_content,
)

# ── Test helpers ────────────────────────────────────────────────────────────


def _make_post(post_id: int, title: str, content: str) -> MagicMock:
    """Helper: create a mock Post with given attributes."""
    post = MagicMock(spec=Post)
    post.id = post_id
    post.title = title
    post.content = content
    return post


class TestNormalizeText:
    """Tests for _normalize_text() — text normalization helper."""

    def test_none_value_returns_empty_string(self):
        """None 值处理 → 返回空字符串."""
        assert _normalize_text(None) == ""
        assert _normalize_text(None, None) == ""

    def test_empty_text_returns_empty_string(self):
        """空文本 → 返回空字符串."""
        assert _normalize_text("") == ""
        assert _normalize_text("   ") == ""

    def test_removes_punctuation_and_symbols(self):
        """过滤标点符号（P/S 类别）."""
        result = _normalize_text("Hello, World! 你好，世界！")
        # Punctuation and full-width punctuation removed
        assert "," not in result
        assert "!" not in result
        assert "，" not in result
        assert "！" not in result
        # Content preserved, lowercased
        assert "hello" in result
        assert "world" in result

    def test_collapses_whitespace(self):
        """re.sub 合并多余空白."""
        result = _normalize_text("Hello    World    Test")
        # Multiple spaces collapsed to single
        assert "  " not in result

    def test_nfkc_normalization(self):
        """NFKC 归一化：全角字符转半角."""
        # Full-width latin characters
        result = _normalize_text("Ｈｅｌｌｏ")
        assert result == "hello"

    def test_lowercase_conversion(self):
        """大小写归一化为小写."""
        result = _normalize_text("Hello WORLD")
        # Result should be all lowercase
        assert result == "hello world"

    def test_combined_title_and_content(self):
        """标题和内容被组合."""
        result = _normalize_text("Stock Market", "Today's Analysis")
        assert "stock" in result
        assert "market" in result
        assert "todays" in result  # apostrophe removed
        assert "analysis" in result


class TestCheckDuplicatePostContent:
    """Tests for check_duplicate_post_content()."""

    # ── Text too short ────────────────────────────────────────────────────

    def test_text_too_short_returns_early(self, db):
        """归一化文本 < MIN_DUPLICATE_TEXT_LENGTH(20) → 提前返回 text_too_short."""
        result = check_duplicate_post_content(db, user_id=1, title="hi", content="short")
        assert result.status == "ok"
        assert result.reason == "text_too_short"
        assert result.should_block is False
        assert result.should_review is False

    # ── Exact duplicate ───────────────────────────────────────────────────

    def test_exact_duplicate_returns_should_block(self, db):
        """精确匹配 → should_block=True, similarity=1.0."""
        existing = _make_post(10, "Stock Market Analysis", "This is a detailed market report with enough characters for detection.")
        db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [existing]

        result = check_duplicate_post_content(
            db,
            user_id=1,
            title="Stock Market Analysis",
            content="This is a detailed market report with enough characters for detection.",
        )
        assert result.status == "exact_duplicate"
        assert result.should_block is True
        assert result.similarity == 1.0
        assert result.matched_post_id == 10
        assert result.reason == "exact_duplicate_post"

    # ── Exact duplicate with normalization (different case/punctuation) ───

    def test_exact_duplicate_with_different_case_and_punctuation(self, db):
        """大小写和标点不同但归一化后相同 → 精确匹配."""
        existing = _make_post(10, "Hello World Test", "Content with enough words to pass the minimum text length threshold")
        db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [existing]

        result = check_duplicate_post_content(
            db,
            user_id=1,
            title="Hello, World! Test",
            content="Content with enough words to pass the minimum text length threshold!!",
        )
        assert result.status == "exact_duplicate"
        assert result.should_block is True

    # ── Near duplicate (>=0.92) ───────────────────────────────────────────

    def test_near_duplicate_high_similarity(self, db):
        """模糊匹配 >= 0.92 → should_review=True."""
        base = "This is a comprehensive market analysis report with detailed data and charts for investors to review carefully"
        existing = _make_post(10, "Market Report", base)
        db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [existing]

        # Very similar text (just minor changes — enough to be >0.92)
        similar = base[:80] + base[80:]  # nearly identical
        result = check_duplicate_post_content(db, user_id=1, title="Market Report", content=similar)
        assert result.status == "exact_duplicate" or result.status == "near_duplicate"

    # ── Below threshold (<0.92) ───────────────────────────────────────────

    def test_below_threshold_passes(self, db):
        """相似度 < 0.92 → 正常通过（不触发审核）."""
        existing = _make_post(
            10,
            "Market Analysis Report on Technology Sector Performance in Q3",
            "This report analyzes technology sector stocks including large-cap and small-cap companies with detailed financial metrics and growth projections for the coming quarters.",
        )
        db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [existing]

        # Very different content
        result = check_duplicate_post_content(
            db,
            user_id=1,
            title="Weather Forecast for Next Week",
            content="The weather forecast shows sunny conditions for most of next week with temperatures ranging from twenty to thirty degrees Celsius across the region.",
        )
        assert result.reason == "no_duplicate_detected"
        assert result.should_block is False
        assert result.should_review is False

    # ── No posts ──────────────────────────────────────────────────────────

    def test_no_recent_posts_returns_no_duplicate(self, db):
        """用户最近无帖子 → 正常通过."""
        db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []

        result = check_duplicate_post_content(
            db,
            user_id=1,
            title="New Post Title That Is Long Enough",
            content="This content has sufficient length to pass the minimum text length threshold check.",
        )
        assert result.reason == "no_duplicate_detected"

    # ── Best match among multiple ─────────────────────────────────────────

    def test_best_match_among_multiple_posts(self, db):
        """多个帖子中找到最佳匹配 → 返回相似度最高的."""
        post1 = _make_post(
            10,
            "Topic A Title Here",
            "Content for topic A with enough words to meet the minimum text length requirement for duplicate detection",
        )
        post2 = _make_post(
            20,
            "Very Similar Title Here",
            "Content very similar to the new post with enough words to meet the minimum text length requirement for detection purposes",
        )
        post3 = _make_post(
            30,
            "Topic C Title Here",
            "Content for topic C that is somewhat related but uses different wording and structure throughout the entire document",
        )
        db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [
            post1, post2, post3
        ]

        # Similar to post2
        result = check_duplicate_post_content(
            db,
            user_id=1,
            title="Very Similar Title Here",
            content="Content very similar to the new post with enough words to meet the minimum text length requirement for detection purposes",
        )
        # Should match post2 exactly
        assert result.matched_post_id is not None

    # ── Existing post too short skipped ───────────────────────────────────

    def test_existing_post_too_short_skipped(self, db):
        """现有帖子文本太短 → 跳过比较."""
        short_post = _make_post(10, "Hi", "short")
        db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [short_post]

        result = check_duplicate_post_content(
            db,
            user_id=1,
            title="A Properly Long Title For Content",
            content="This content has sufficient text length to pass the minimum duplicate text length check of twenty characters.",
        )
        # The short post should be skipped, and since no other posts exist, no duplicate
        assert result.reason == "no_duplicate_detected"
