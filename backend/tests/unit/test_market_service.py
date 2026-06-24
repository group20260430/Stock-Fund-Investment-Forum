"""Unit tests for Market API — index data proxy with fallback."""

import httpx
import pytest
import respx

from app.api.market import get_indices, get_kline


class TestGetIndices:
    """Tests for get_indices() — async index data endpoint."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_eastmoney_success(self):
        """东方财富正常 → 返回东方财富格式数据."""
        route = respx.get("https://push2.eastmoney.com/api/qt/ulist.np/get")
        route.respond(
            json={
                "data": {
                    "diff": [
                        {
                            "f2": 3100.50,
                            "f3": 0.50,
                            "f4": 15.20,
                            "f12": "000001",
                            "f14": "上证指数",
                            "f15": 3105.0,
                            "f16": 3090.0,
                            "f17": 3095.0,
                            "f18": 3085.30,
                            "f5": 250000000,
                            "f6": 3200000000.0,
                        }
                    ]
                }
            },
            status_code=200,
        )

        result = await get_indices(secids="1.000001")
        assert result["code"] == 200
        assert result["data"][0]["code"] == "000001"
        assert result["data"][0]["price"] == 3100.50
        assert result["data"][0]["change"] == 15.20
        assert result["data"][0]["change_pct"] == 0.50
        assert result["data"][0]["up"] is True

    @respx.mock
    @pytest.mark.asyncio
    async def test_eastmoney_timeout_falls_back_to_sina(self):
        """东方财富超时 → 自动降级到新浪财经."""
        # Eastmoney timeout
        respx.get("https://push2.eastmoney.com/api/qt/ulist.np/get").mock(
            side_effect=httpx.TimeoutException("timeout")
        )

        # Sina fallback succeeds
        sina_route = respx.get("https://hq.sinajs.cn/list=s_sh000001")
        sina_content = (
            'var hq_str_s_sh000001="上证指数,3100.50,15.20,0.50,250000000,3200000000";'
        )
        sina_route.respond(
            content=sina_content.encode("gb18030"),
            status_code=200,
        )

        result = await get_indices(secids="1.000001")
        assert result["code"] == 200
        assert "sina" in result["message"].lower()
        assert len(result["data"]) > 0

    @respx.mock
    @pytest.mark.asyncio
    async def test_both_sources_fail_returns_fallback(self):
        """两个数据源都失败 → 返回空数据标记."""
        # Both sources fail
        respx.get("https://push2.eastmoney.com/api/qt/ulist.np/get").mock(
            side_effect=httpx.TimeoutException("timeout")
        )
        respx.get("https://hq.sinajs.cn/list=s_sh000001").mock(
            side_effect=httpx.ConnectError("connection refused")
        )

        result = await get_indices(secids="1.000001")
        assert result["code"] == 200
        assert "fallback" in result["message"].lower()
        assert result["data"][0]["code"] == "000001"
        # Fallback data has null prices
        assert result["data"][0]["price"] is None

    @respx.mock
    @pytest.mark.asyncio
    async def test_eastmoney_empty_data_falls_back(self):
        """东方财富返回空 data → 降级到新浪."""
        # Eastmoney returns data but diff is None
        respx.get("https://push2.eastmoney.com/api/qt/ulist.np/get").respond(
            json={"data": None},
            status_code=200,
        )

        # Sina fallback succeeds
        sina_content = (
            'var hq_str_s_sh000001="上证指数,3100.50,15.20,0.50,250000000,3200000000";'
        )
        respx.get("https://hq.sinajs.cn/list=s_sh000001").respond(
            content=sina_content.encode("gb18030"),
            status_code=200,
        )

        result = await get_indices(secids="1.000001")
        assert result["code"] == 200
        assert "sina" in result["message"].lower()

    @respx.mock
    @pytest.mark.asyncio
    async def test_multiple_indices(self):
        """多个指数查询 → 返回多个结果."""
        respx.get("https://push2.eastmoney.com/api/qt/ulist.np/get").respond(
            json={
                "data": {
                    "diff": [
                        {
                            "f2": 3100.50, "f3": 0.50, "f4": 15.20,
                            "f12": "000001", "f14": "上证指数",
                            "f15": 3105.0, "f16": 3090.0, "f17": 3095.0,
                            "f18": 3085.30, "f5": 250000000, "f6": 3200000000.0,
                        },
                        {
                            "f2": 4000.00, "f3": -0.30, "f4": -12.00,
                            "f12": "000300", "f14": "沪深300",
                            "f15": 4020.0, "f16": 3990.0, "f17": 4010.0,
                            "f18": 4012.00, "f5": 150000000, "f6": 2000000000.0,
                        },
                    ]
                }
            },
            status_code=200,
        )

        result = await get_indices(secids="1.000001,1.000300")
        assert result["code"] == 200
        assert len(result["data"]) == 2
        # Check second index
        assert result["data"][1]["code"] == "000300"
        assert result["data"][1]["up"] is False  # negative change_pct

    @respx.mock
    @pytest.mark.asyncio
    async def test_default_indices_when_no_secids(self):
        """不传 secids → 使用默认指数列表."""
        respx.get("https://push2.eastmoney.com/api/qt/ulist.np/get").respond(
            json={
                "data": {
                    "diff": [
                        {
                            "f2": 3100.50, "f3": 0.50, "f4": 15.20,
                            "f12": "000001", "f14": "上证指数",
                            "f15": 3105.0, "f16": 3090.0, "f17": 3095.0,
                            "f18": 3085.30, "f5": 250000000, "f6": 3200000000.0,
                        },
                        {
                            "f2": 4000.00, "f3": 0.20, "f4": 8.00,
                            "f12": "000300", "f14": "沪深300",
                            "f15": 4020.0, "f16": 3990.0, "f17": 4010.0,
                            "f18": 3992.00, "f5": 150000000, "f6": 2000000000.0,
                        },
                        {
                            "f2": 11000.00, "f3": -0.50, "f4": -55.00,
                            "f12": "399001", "f14": "深证成指",
                            "f15": 11100.0, "f16": 10950.0, "f17": 11050.0,
                            "f18": 11055.00, "f5": 180000000, "f6": 2500000000.0,
                        },
                    ]
                }
            },
            status_code=200,
        )

        result = await get_indices()  # no secids → uses DEFAULT_INDICES
        assert result["code"] == 200
        assert len(result["data"]) == 3

    @respx.mock
    @pytest.mark.asyncio
    async def test_specific_index_code(self):
        """特定指数代码：000001(上证), 399001(深证成指)."""
        respx.get("https://push2.eastmoney.com/api/qt/ulist.np/get").respond(
            json={
                "data": {
                    "diff": [
                        {
                            "f2": 11000.00, "f3": 1.50, "f4": 165.00,
                            "f12": "399001", "f14": "深证成指",
                            "f15": 11100.0, "f16": 10950.0, "f17": 11050.0,
                            "f18": 10835.00, "f5": 180000000, "f6": 2500000000.0,
                        }
                    ]
                }
            },
            status_code=200,
        )

        result = await get_indices(secids="0.399001")
        assert result["code"] == 200
        assert result["data"][0]["code"] == "399001"
        assert result["data"][0]["change_pct"] == 1.50


class TestGetKline:
    """Tests for get_kline() — async K-line data endpoint."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_kline_normal(self):
        """正常K线数据 → 返回解析后的 points."""
        kline_data = (
            "2025-06-20,3095.00,3100.50,3105.00,3090.00,250000000,3200000000.00\n"
            "2025-06-23,3100.50,3110.00,3115.00,3098.00,260000000,3400000000.00\n"
            "2025-06-24,3110.00,3095.00,3112.00,3085.00,280000000,3500000000.00"
        )
        respx.get("https://push2his.eastmoney.com/api/qt/stock/kline/get").respond(
            json={
                "data": {
                    "klines": kline_data.split("\n"),
                }
            },
            status_code=200,
        )

        result = await get_kline(secid="1.000001", klt=101, lmt=20)
        assert result["code"] == 200
        assert len(result["data"]) == 3
        assert result["data"][0]["date"] == "2025-06-20"
        assert result["data"][0]["open"] == 3095.00
        assert result["data"][0]["close"] == 3100.50
        assert result["data"][0]["high"] == 3105.00
        assert result["data"][0]["low"] == 3090.00
        assert result["data"][0]["volume"] == 250000000

    @respx.mock
    @pytest.mark.asyncio
    async def test_kline_empty_response(self):
        """K线返回空 data → 返回空数组."""
        respx.get("https://push2his.eastmoney.com/api/qt/stock/kline/get").respond(
            json={"data": None},
            status_code=200,
        )

        result = await get_kline(secid="1.000001")
        assert result["code"] == 200
        assert result["data"] == []

    @respx.mock
    @pytest.mark.asyncio
    async def test_kline_network_error(self):
        """K线网络错误 → 返回 500 错误."""
        respx.get("https://push2his.eastmoney.com/api/qt/stock/kline/get").mock(
            side_effect=httpx.ConnectError("connection refused")
        )

        result = await get_kline(secid="1.000001")
        assert result["code"] == 500
        assert result["data"] == []

    @respx.mock
    @pytest.mark.asyncio
    async def test_kline_different_periods(self):
        """不同K线周期：日线(klt=101), 周线(klt=102)."""
        route = respx.get("https://push2his.eastmoney.com/api/qt/stock/kline/get")
        route.respond(
            json={"data": {"klines": ["2025-06-20,100.00,101.00,102.00,99.00,10000,1000000.00"]}},
            status_code=200,
        )

        # Daily
        result_daily = await get_kline(secid="1.000001", klt=101, lmt=20)
        assert result_daily["code"] == 200
        assert len(result_daily["data"]) == 1

        # Weekly
        result_weekly = await get_kline(secid="1.000001", klt=102, lmt=10)
        assert result_weekly["code"] == 200
        assert len(result_weekly["data"]) == 1

    @respx.mock
    @pytest.mark.asyncio
    async def test_kline_partial_data_skipped(self):
        """部分K线数据字段不足5个 → 跳过该行."""
        kline_data = (
            "2025-06-20,3095.00,3100.50,3105.00,3090.00,250000000,3200000000.00\n"  # valid
            "incomplete,line"  # fewer than 5 parts → skipped
        )
        respx.get("https://push2his.eastmoney.com/api/qt/stock/kline/get").respond(
            json={
                "data": {
                    "klines": kline_data.split("\n"),
                }
            },
            status_code=200,
        )

        result = await get_kline(secid="1.000001")
        assert result["code"] == 200
        # Only the valid line should be parsed
        assert len(result["data"]) == 1
        assert result["data"][0]["date"] == "2025-06-20"
