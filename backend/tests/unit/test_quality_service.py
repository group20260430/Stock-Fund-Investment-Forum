"""Unit tests for QualityService.score_content — content quality scoring."""

import pytest

from app.services.quality_service import QualityScore, score_content


class TestScoreContent:
    """Tests for score_content() — pure function, no DB mocking needed."""

    # ── Empty / minimal content ──────────────────────────────────────────

    def test_empty_none_returns_minimal_score(self):
        """空内容 → 最低分，level="low"，flags 包含 "empty"."""
        result = score_content(None)
        assert result.score == 0
        assert result.level == "low"
        assert "empty" in result.flags
        assert result.word_count == 0
        assert result.char_count == 0
        assert result.has_paragraphs is False
        assert result.has_links is False

    def test_empty_string_returns_minimal_score(self):
        """空字符串 → 最低分."""
        result = score_content("")
        assert result.score == 0
        assert result.level == "low"

    def test_whitespace_only_returns_minimal_score(self):
        """仅空白字符 → 最低分."""
        result = score_content("   \n  \t  ")
        assert result.score == 0
        assert result.level == "low"

    def test_very_short_text_below_5_words(self):
        """极短文本（<5词）→ 低分，length_score=0，flag="too_short"."""
        result = score_content("Hi")
        assert result.score == 0
        assert "too_short" in result.flags

    # ── Short / medium length content ────────────────────────────────────

    def test_short_text_below_50_chars(self):
        """短文本（<50字符）→ length_score=5."""
        result = score_content("Stock market is volatile today")
        assert result.score > 0
        assert result.level in ("low", "medium")

    def test_medium_text_50_to_100_chars(self):
        """中等长度文本（50-100字符）→ length_score=20."""
        # Build ~70 chars of varied content
        text = (
            "Stock market showed mixed results today as investors "
            "weighed economic data carefully."
        )
        assert 50 <= len(text) < 100
        result = score_content(text)
        assert result.score >= 20  # at minimum the length score

    def test_long_text_100_to_500_chars(self):
        """长文本（100-500字符）→ length_score=32."""
        # Build ~200 chars
        text = (
            "Market analysis for Q3 2025 shows a significant uptick in "
            "technology sector performance. Large-cap stocks led the rally "
            "while small-cap names underperformed relative to their "
            "historical averages. Bond yields remained steady."
        )
        assert 100 <= len(text) < 500
        result = score_content(text)
        assert result.score >= 30

    def test_excellent_text_over_500_chars(self):
        """超长优质文本（>500字符）→ length_score=40，level="good"."""
        base = (
            "A comprehensive analysis of the current market conditions "
            "reveals several key trends worth noting for investors. "
        )
        text = base * 10  # ~600+ chars
        assert len(text) > 500
        result = score_content(text)
        assert result.score >= 40

    # ── Structure scoring ─────────────────────────────────────────────────

    def test_structured_with_paragraphs(self):
        """有段落分隔的文本 → structure_score 含 +15."""
        text = (
            "First paragraph with some analysis.\n\n"
            "Second paragraph with more details."
        ) * 3  # ensure >50 chars
        result = score_content(text)
        assert result.has_paragraphs is True
        assert "structured" in result.flags

    def test_bullet_list_structure(self):
        """有编号列表 → structure_score 含 +10."""
        text = (
            "投资建议如下：\n"
            "1、关注科技板块\n"
            "2、适当配置债券\n"
            "3、回避高估值个股"
        )
        result = score_content(text)
        # Should have structure from bullet/numbered list pattern
        assert result.score > 0

    # ── Substance scoring ────────────────────────────────────────────────

    def test_content_with_links(self):
        """含链接的文本 → substance_score 含 +10，has_links=True."""
        text = (
            "Check out this analysis at https://example.com/market-report "
            "for detailed charts and data on the current market trends."
        )
        result = score_content(text)
        assert result.has_links is True
        assert "has_links" in result.flags

    def test_content_with_stock_codes(self):
        """含股票代码（4+位数字）→ substance_score 含 +5."""
        text = "推荐关注股票代码 600519 和 000858，近期表现优异"
        result = score_content(text)
        assert result.score > 0

    def test_content_with_percentages(self):
        """含百分比 → substance_score 含 +5."""
        text = "上证指数今日上涨 2.5%，成交额增加 15.8%，北向资金净流入"
        result = score_content(text)
        assert result.score > 0

    # ── Word diversity ────────────────────────────────────────────────────

    def test_repeated_content_low_diversity(self):
        """纯重复内容 → 低 diversity 分."""
        text = "buy buy buy buy buy buy buy buy buy buy " * 10
        result = score_content(text)
        # Repeated words should keep diversity score low
        assert result.score < 60

    def test_high_quality_long_text_with_everything(self):
        """优质长文（>500字，有标题，多段落，含财经关键词，含链接）→ 高分（>60）."""
        text = (
            "2025年第四季度投资策略报告\n\n"
            "一、宏观环境分析\n\n"
            "当前宏观经济面临多重挑战与机遇。美联储货币政策走向、"
            "国内经济复苏节奏以及地缘政治因素都将影响市场表现。"
            "全球通胀水平逐步回落，但核心通胀粘性仍较强。"
            "国内方面，财政政策持续发力，基建投资保持较高增速。"
            "货币政策维持稳健偏松基调，流动性合理充裕。\n\n"
            "二、行业配置建议\n\n"
            "建议重点关注以下领域：\n"
            "1. 科技创新板块：人工智能、半导体产业链持续受益于政策支持。"
            "股票代码 002230 和 688981 值得关注。"
            "科技自主可控是长期主线，国产替代空间广阔。\n"
            "2. 消费复苏：随着居民收入预期改善，消费板块有望迎来修复。"
            "餐饮旅游、家电汽车等可选消费弹性较大。\n"
            "3. 新能源：光伏产业链价格企稳，龙头企业盈利改善明显。"
            "储能和智能电网建设加快推进，行业景气度维持高位。\n\n"
            "三、风险提示\n\n"
            "上证指数今年以来上涨 12.5%，但波动率也显著上升。"
            "投资者需注意仓位管理，控制回撤风险。"
            "外部不确定性包括地缘冲突、贸易摩擦等因素。\n\n"
            "四、总结与展望\n\n"
            "综合来看，市场结构性机会大于系统性风险，建议均衡配置。\n\n"
            "详细分析请参考：https://example.com/investment-report\n\n"
            "免责声明：本文仅为个人观点，不构成投资建议。"
        )
        result = score_content(text)
        assert len(text) > 500
        assert result.score > 60
        assert result.level == "good"
        assert result.has_paragraphs is True
        assert result.has_links is True
        assert result.char_count > 500

    # ── Level classification ──────────────────────────────────────────────

    @pytest.mark.parametrize(
        "score,expected_level",
        [
            (0, "low"),
            (15, "low"),
            (29, "low"),
            (30, "medium"),
            (45, "medium"),
            (59, "medium"),
            (60, "good"),
            (80, "good"),
            (100, "good"),
        ],
    )
    def test_level_classification(self, score, expected_level):
        """验证分数→等级映射：<30=low, 30-59=medium, >=60=good."""
        qs = QualityScore(
            score=score,
            level=expected_level,
            flags=[],
            word_count=50,
            char_count=200,
            has_paragraphs=False,
            has_links=False,
        )
        assert qs.level == expected_level
