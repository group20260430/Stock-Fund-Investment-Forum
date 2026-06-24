"""Unit tests for ComplianceService — regex-based compliance rule detection."""

from unittest.mock import MagicMock

from app.models.operations import ComplianceCategory, ComplianceRule, SensitiveLevel
from app.services.compliance_service import (
    ComplianceMatch,
    check_compliance,
    check_compliance_single_text,
)


def _make_rule(
    rule_id: int,
    name: str,
    pattern: str,
    severity: SensitiveLevel,
    category: ComplianceCategory,
    is_active: bool = True,
    description: str | None = None,
) -> MagicMock:
    """Helper: create a mock ComplianceRule with given attributes."""
    rule = MagicMock(spec=ComplianceRule)
    rule.id = rule_id
    rule.name = name
    rule.pattern = pattern
    rule.severity = severity
    rule.category = category
    rule.is_active = is_active
    rule.description = description
    return rule


class TestComplianceService:
    """Tests for check_compliance() and check_compliance_single_text()."""

    # ── Stock recommendation ──────────────────────────────────────────────

    def test_stock_recommendation_regex_match(self, db):
        """"推荐大家买入XXXX股票" → 触发荐股规则."""
        rule = _make_rule(
            1,
            "Stock Recommendation",
            r"[推荐推].{0,5}(买|入|增).{0,5}\d{6}",
            SensitiveLevel.BLOCK,
            ComplianceCategory.STOCK_RECOMMENDATION,
        )
        db.query.return_value.filter.return_value.all.return_value = [rule]

        result = check_compliance(db, ["推荐大家买入600519股票"])
        assert result.level == SensitiveLevel.BLOCK
        assert result.should_block is True
        assert len(result.matches) == 1
        assert result.matches[0].category == ComplianceCategory.STOCK_RECOMMENDATION

    # ── Market manipulation ───────────────────────────────────────────────

    def test_market_manipulation_regex_match(self, db):
        """"我们一起拉升这支票" → 触发市场操纵规则."""
        rule = _make_rule(
            2,
            "Market Manipulation",
            r"(拉升|砸盘|抬轿|对倒).{0,5}(股价|这支|这票|该股)",
            SensitiveLevel.BLOCK,
            ComplianceCategory.MARKET_MANIPULATION,
        )
        db.query.return_value.filter.return_value.all.return_value = [rule]

        result = check_compliance(db, ["我们一起拉升这支票"])
        assert result.level == SensitiveLevel.BLOCK
        assert len(result.matches) == 1
        assert result.matches[0].category == ComplianceCategory.MARKET_MANIPULATION

    # ── No match ──────────────────────────────────────────────────────────

    def test_no_match_returns_empty(self, db):
        """"今天天气不错，适合投资" → 不触发规则."""
        rule = _make_rule(
            1,
            "Stock Recommendation",
            r"推荐.{0,10}\d{6}",
            SensitiveLevel.BLOCK,
            ComplianceCategory.STOCK_RECOMMENDATION,
        )
        db.query.return_value.filter.return_value.all.return_value = [rule]

        result = check_compliance(db, ["今天天气不错，适合投资"])
        assert result.level is None
        assert result.matches == []
        assert result.should_block is False

    # ── Disabled rules ────────────────────────────────────────────────────

    def test_disabled_rule_skipped(self, db):
        """禁用规则不应生效（SQLAlchemy filter 会排除 is_active=False 的规则）."""
        # The real DB filter .filter(ComplianceRule.is_active.is_(True))
        # would exclude inactive rules, so we simulate the DB returning nothing.
        db.query.return_value.filter.return_value.all.return_value = []

        result = check_compliance(db, ["推荐买入600519"])
        assert result.level is None

    # ── Multiple rules, highest severity ──────────────────────────────────

    def test_multiple_rules_highest_severity_wins(self, db):
        """多个规则同时匹配 → 返回最高级别处理."""
        review_rule = _make_rule(
            1,
            "Rule A",
            r"买入\d{6}",
            SensitiveLevel.REVIEW,
            ComplianceCategory.STOCK_RECOMMENDATION,
        )
        block_rule = _make_rule(
            2,
            "Rule B",
            r"推荐",
            SensitiveLevel.BLOCK,
            ComplianceCategory.STOCK_RECOMMENDATION,
        )
        db.query.return_value.filter.return_value.all.return_value = [review_rule, block_rule]

        result = check_compliance(db, ["推荐买入600519"])
        assert result.level == SensitiveLevel.BLOCK
        assert result.should_block is True
        assert len(result.matches) == 2

    # ── Chinese regex ─────────────────────────────────────────────────────

    def test_chinese_regex_matching(self, db):
        """中文正则匹配验证."""
        rule = _make_rule(
            1,
            "Chinese Pattern",
            r"代客.{0,5}理财",
            SensitiveLevel.BLOCK,
            ComplianceCategory.STOCK_RECOMMENDATION,
        )
        db.query.return_value.filter.return_value.all.return_value = [rule]

        result = check_compliance(db, ["本工作室代客理财，收益保底"])
        assert result.should_block is True

    # ── Invalid regex pattern ─────────────────────────────────────────────

    def test_invalid_regex_pattern_handled_gracefully(self, db):
        """无效正则表达式被忽略，不抛异常."""
        rule = _make_rule(
            1,
            "Broken Rule",
            r"[unclosed",  # invalid regex
            SensitiveLevel.BLOCK,
            ComplianceCategory.STOCK_RECOMMENDATION,
        )
        db.query.return_value.filter.return_value.all.return_value = [rule]

        # Should not raise, just skip the broken rule
        result = check_compliance(db, ["some text"])
        assert result.level is None
        assert result.matches == []

    # ── Empty input ───────────────────────────────────────────────────────

    def test_empty_texts_returns_empty(self, db):
        """空文本列表 → 正常通过."""
        rule = _make_rule(
            1, "Rule", r"pattern", SensitiveLevel.BLOCK, ComplianceCategory.STOCK_RECOMMENDATION
        )
        db.query.return_value.filter.return_value.all.return_value = [rule]

        result = check_compliance(db, [None, "", "   "])
        assert result.level is None

    # ── No active rules ───────────────────────────────────────────────────

    def test_no_active_rules_returns_empty(self, db):
        """无激活规则 → 正常通过."""
        db.query.return_value.filter.return_value.all.return_value = []

        result = check_compliance(db, ["任何内容"])
        assert result.level is None

    # ── Single text helper ────────────────────────────────────────────────

    def test_check_compliance_single_text(self, db):
        """check_compliance_single_text 便捷封装正确传参."""
        rule = _make_rule(
            1, "R", r"test", SensitiveLevel.REVIEW, ComplianceCategory.STOCK_RECOMMENDATION
        )
        db.query.return_value.filter.return_value.all.return_value = [rule]

        result = check_compliance_single_text(db, "this is a test")
        assert result.level == SensitiveLevel.REVIEW
        assert len(result.matches) == 1

    # ── Multiple texts ────────────────────────────────────────────────────

    def test_multiple_texts_match_across_texts(self, db):
        """跨多文本匹配，每条规则每条文本只匹配一次."""
        rule = _make_rule(
            1, "R", r"\d{6}", SensitiveLevel.REVIEW, ComplianceCategory.STOCK_RECOMMENDATION
        )
        db.query.return_value.filter.return_value.all.return_value = [rule]

        result = check_compliance(db, [
            "文本A包含600519",
            "文本B包含000858",
        ])
        assert len(result.matches) >= 1

    def test_categories_property(self, db):
        """验证 categories 属性返回去重列表."""
        rule1 = _make_rule(
            1, "R1", r"股票", SensitiveLevel.REVIEW, ComplianceCategory.STOCK_RECOMMENDATION
        )
        rule2 = _make_rule(
            2, "R2", r"拉升", SensitiveLevel.BLOCK, ComplianceCategory.MARKET_MANIPULATION
        )
        db.query.return_value.filter.return_value.all.return_value = [rule1, rule2]

        result = check_compliance(db, ["股票拉升策略"])
        categories = result.categories
        assert isinstance(categories, list)
        assert ComplianceCategory.STOCK_RECOMMENDATION.value in categories
        assert ComplianceCategory.MARKET_MANIPULATION.value in categories
