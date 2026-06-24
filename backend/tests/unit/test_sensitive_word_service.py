"""Unit tests for SensitiveWordService — sensitive word detection."""

from unittest.mock import MagicMock

import pytest

from app.models.operations import SensitiveLevel, SensitiveWord
from app.services.sensitive_word_service import SensitiveCheckResult, check_sensitive_texts


def _make_word(word: str, level: SensitiveLevel, is_active: bool = True) -> MagicMock:
    """Helper: create a mock SensitiveWord with given attributes."""
    sw = MagicMock(spec=SensitiveWord)
    sw.word = word
    sw.level = level
    sw.is_active = is_active
    return sw


class TestSensitiveWordService:
    """Tests for check_sensitive_texts()."""

    # ── BLOCK level ───────────────────────────────────────────────────────

    def test_block_level_returns_should_block(self, db):
        """BLOCK 级别命中 → should_block=True."""
        block_word = _make_word("禁发词", SensitiveLevel.BLOCK)
        db.query.return_value.filter.return_value.all.return_value = [block_word]

        result = check_sensitive_texts(db, ["这是包含禁发词的内容"])
        assert result.should_block is True
        assert result.should_review is False
        assert result.level == SensitiveLevel.BLOCK
        assert "禁发词" in result.matched_words

    # ── REVIEW level ──────────────────────────────────────────────────────

    def test_review_level_returns_should_review(self, db):
        """REVIEW 级别命中 → should_review=True."""
        review_word = _make_word("审核词", SensitiveLevel.REVIEW)
        db.query.return_value.filter.return_value.all.return_value = [review_word]

        result = check_sensitive_texts(db, ["需要审核词检查"])
        assert result.should_review is True
        assert result.should_block is False
        assert result.level == SensitiveLevel.REVIEW

    # ── WARN level ────────────────────────────────────────────────────────

    def test_warn_level_no_block_or_review(self, db):
        """WARN 级别命中 → 仅警告，不拦截也不审核."""
        warn_word = _make_word("提醒词", SensitiveLevel.WARN)
        db.query.return_value.filter.return_value.all.return_value = [warn_word]

        result = check_sensitive_texts(db, ["包含提醒词的内容"])
        assert result.should_block is False
        assert result.should_review is False
        assert result.level == SensitiveLevel.WARN
        assert "提醒词" in result.matched_words

    # ── Multiple words, highest priority ──────────────────────────────────

    def test_multiple_words_returns_highest_priority(self, db):
        """多个敏感词同时命中 → 返回最高级别（BLOCK > REVIEW > WARN）."""
        words = [
            _make_word("警告词", SensitiveLevel.WARN),
            _make_word("审核词", SensitiveLevel.REVIEW),
            _make_word("拦截词", SensitiveLevel.BLOCK),
        ]
        db.query.return_value.filter.return_value.all.return_value = words

        result = check_sensitive_texts(db, ["包含拦截词和审核词和警告词"])
        assert result.level == SensitiveLevel.BLOCK
        assert result.should_block is True
        assert len(result.matched_words) == 3

    # ── Inactive word skipped ─────────────────────────────────────────────

    def test_inactive_word_skipped(self, db):
        """停用词（is_active=False）→ 不触发检测（SQLAlchemy filter 会排除）."""
        # Since the DB filter .filter(SensitiveWord.is_active.is_(True))
        # would exclude inactive words, we simulate the DB returning no results.
        db.query.return_value.filter.return_value.all.return_value = []

        result = check_sensitive_texts(db, ["任何内容"])
        assert result.level is None
        assert len(result.matched_words) == 0

    # ── Chinese matching ──────────────────────────────────────────────────

    def test_chinese_word_matching(self, db):
        """中文敏感词匹配：内容包含"违禁" → 拦截."""
        word = _make_word("违禁", SensitiveLevel.BLOCK)
        db.query.return_value.filter.return_value.all.return_value = [word]

        result = check_sensitive_texts(db, ["这篇文章包含违禁内容"])
        assert result.should_block is True
        assert "违禁" in result.matched_words

    # ── English matching ──────────────────────────────────────────────────

    def test_english_word_matching_case_insensitive(self, db):
        """英文敏感词匹配：大小写不敏感."""
        word = _make_word("spam", SensitiveLevel.BLOCK)
        db.query.return_value.filter.return_value.all.return_value = [word]

        result = check_sensitive_texts(db, ["This is SPAM content"])
        assert result.should_block is True
        assert "spam" in result.matched_words

    # ── Empty content ─────────────────────────────────────────────────────

    def test_empty_content_returns_no_match(self, db):
        """空内容 → 正常通过，无匹配."""
        word = _make_word("禁发词", SensitiveLevel.BLOCK)
        db.query.return_value.filter.return_value.all.return_value = [word]

        result = check_sensitive_texts(db, [""])
        assert result.level is None
        assert result.matched_words == []

    def test_none_content_returns_no_match(self, db):
        """None 内容 → 正常通过."""
        word = _make_word("禁发词", SensitiveLevel.BLOCK)
        db.query.return_value.filter.return_value.all.return_value = [word]

        result = check_sensitive_texts(db, [None])
        assert result.level is None

    # ── No active words ───────────────────────────────────────────────────

    def test_no_active_words_returns_no_match(self, db):
        """数据库无激活敏感词 → 正常通过."""
        db.query.return_value.filter.return_value.all.return_value = []

        result = check_sensitive_texts(db, ["任何内容"])
        assert result.level is None
        assert result.matched_words == []

    # ── Multiple texts ────────────────────────────────────────────────────

    def test_multiple_texts_at_least_one_matches(self, db):
        """多个文本中至少一个命中 → 返回匹配."""
        block_word = _make_word("禁发词", SensitiveLevel.BLOCK)
        db.query.return_value.filter.return_value.all.return_value = [block_word]

        result = check_sensitive_texts(db, [
            None,
            "",
            "正常内容",
            "包含禁发词的文本",
        ])
        assert result.should_block is True
        assert "禁发词" in result.matched_words


class TestSensitiveCheckResult:
    """Tests for SensitiveCheckResult dataclass properties."""

    def test_no_level(self):
        result = SensitiveCheckResult(level=None, matched_words=[])
        assert result.should_block is False
        assert result.should_review is False

    def test_level_warn(self):
        result = SensitiveCheckResult(level=SensitiveLevel.WARN, matched_words=["test"])
        assert result.should_block is False
        assert result.should_review is False

    def test_level_review(self):
        result = SensitiveCheckResult(level=SensitiveLevel.REVIEW, matched_words=["test"])
        assert result.should_block is False
        assert result.should_review is True

    def test_level_block(self):
        result = SensitiveCheckResult(level=SensitiveLevel.BLOCK, matched_words=["test"])
        assert result.should_block is True
        assert result.should_review is False
