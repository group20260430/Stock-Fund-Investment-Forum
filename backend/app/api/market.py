"""
======= 行情数据代理接口 =======
由 FastAPI 代理东方财富实时行情，解决浏览器跨域限制。
"""
import logging
from typing import Optional

import httpx
from fastapi import APIRouter, Query

router = APIRouter(prefix="/market", tags=["market"])

EASTMONEY_QUOTE_URL = "https://push2.eastmoney.com/api/qt/ulist.np/get"
SINA_QUOTE_URL = "https://hq.sinajs.cn/list="

# 默认指数列表
DEFAULT_INDICES = "1.000001,1.000300,0.399001"

# 需要获取的字段
FIELDS = "f2,f3,f4,f5,f6,f12,f14,f15,f16,f17,f18,f20,f21,f170"

# 市场名称映射（用于前端展示）
MARKET_LABELS = {
    "000001": "上证指数",
    "000300": "沪深300",
    "399001": "深证成指",
}

logger = logging.getLogger(__name__)

EASTMONEY_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Referer": "https://quote.eastmoney.com/",
}


@router.get("/indices")
async def get_indices(
    secids: Optional[str] = Query(default=None, description="要查询的证券 ID，逗号分隔：1.000001,1.000300"),
):
    """
    获取实时指数行情数据 — 代理东方财富公开接口。

    返回字段：
      - name:        指数名称
      - code:        指数代码
      - price:       最新价
      - change:      涨跌额
      - change_pct:  涨跌幅 (%)
      - up:          是否上涨 (bool)
      - high:        最高价
      - low:         最低价
      - open:        今开价
      - prev_close:  昨收价
      - volume:      成交量(手)
      - amount:      成交额(元)
    """
    ids = secids or DEFAULT_INDICES

    params = {
        "fltt": "2",
        "secids": ids,
        "fields": FIELDS,
    }

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(EASTMONEY_QUOTE_URL, params=params, headers=EASTMONEY_HEADERS)
            resp.raise_for_status()
            raw = resp.json()
    except httpx.HTTPError as exc:
        logger.error("请求东方财富行情失败: %s", exc)
        return await _get_sina_fallback(ids)
    except Exception as exc:
        logger.error("解析行情数据异常: %s", exc)
        return await _get_sina_fallback(ids)

    if raw is None or raw.get("data") is None:
        return await _get_sina_fallback(ids)

    items = raw["data"].get("diff") or []

    results = []
    for item in items:
        price = item.get("f2", 0) or 0
        prev_close = item.get("f18", 0) or 0
        change_val = item.get("f4", 0) or 0
        change_pct = item.get("f3", 0) or 0
        code = str(item.get("f12", ""))

        results.append(
            {
                "name": MARKET_LABELS.get(code, item.get("f14", "")),
                "code": code,
                "price": round(price, 2),
                "change": round(change_val, 2),
                "change_pct": round(change_pct, 2),
                "up": change_pct >= 0,
                "high": item.get("f15"),
                "low": item.get("f16"),
                "open": item.get("f17"),
                "prev_close": prev_close,
                "volume": item.get("f5"),
                "amount": item.get("f6"),
            }
        )

    return {"code": 200, "message": "success", "data": results}


@router.get("/kline/{secid}")
async def get_kline(
    secid: str,
    klt: int = Query(default=101, description="K线类型：101=日线, 102=周线, 103=月线, 5=5分钟"),
    lmt: int = Query(default=20, description="数据条数"),
):
    """
    获取指定证券的 K 线数据 — 用于迷你走势图
    secid 格式：1.000001（上证指数）
    """
    url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
    params = {
        "secid": secid,
        "klt": klt,
        "fqt": "0",
        "lmt": lmt,
        "fields1": "f1,f2,f3,f4,f5,f6",
        "fields2": "f51,f52,f53,f54,f55,f56,f57",
    }

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(url, params=params, headers=EASTMONEY_HEADERS)
            resp.raise_for_status()
            raw = resp.json()
    except Exception:
        return {"code": 500, "message": "K线数据获取失败", "data": []}

    if raw is None or raw.get("data") is None:
        return {"code": 200, "message": "success", "data": []}

    klines = raw["data"].get("klines") or []

    # 解析 K 线字符串（格式：日期,开盘,收盘,最高,最低,成交量,成交额）
    points = []
    for line in klines:
        parts = line.split(",")
        if len(parts) < 5:
            continue
        points.append(
            {
                "date": parts[0],
                "open": round(float(parts[1]), 2),
                "close": round(float(parts[2]), 2),
                "high": round(float(parts[3]), 2),
                "low": round(float(parts[4]), 2),
                "volume": int(parts[5]) if len(parts) > 5 else 0,
            }
        )

    return {"code": 200, "message": "success", "data": points}


def _build_fallback(secids: str):
    """构建降级数据 — 接口超时或解析失败时使用"""
    ids = [s.strip() for s in secids.split(",")]
    results = []
    for sid in ids:
        code = sid.split(".")[-1]
        results.append(
            {
                "name": MARKET_LABELS.get(code, code),
                "code": code,
                "price": None,
                "change": None,
                "change_pct": None,
                "up": False,
                "high": None,
                "low": None,
                "open": None,
                "prev_close": None,
                "volume": 0,
                "amount": 0,
            }
        )
    return {"code": 200, "message": "success (fallback - API 暂时不可用)", "data": results}


async def _get_sina_fallback(secids: str):
    """Use Sina quotes when Eastmoney rejects the HTTP client connection."""
    requested = [item.strip().split(".")[-1] for item in secids.split(",")]
    symbols = [f"s_{'sh' if code.startswith(('0', '6')) else 'sz'}{code}" for code in requested]
    headers = {
        "User-Agent": EASTMONEY_HEADERS["User-Agent"],
        "Referer": "https://finance.sina.com.cn/",
    }
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.get(SINA_QUOTE_URL + ",".join(symbols), headers=headers)
            response.raise_for_status()
        text = response.content.decode("gb18030")
        results = []
        for line in text.splitlines():
            if '="' not in line:
                continue
            values = line.split('="', 1)[1].rstrip('";').split(",")
            if len(values) < 6:
                continue
            symbol = line.split("hq_str_s_", 1)[1].split("=", 1)[0]
            code = symbol[2:]
            change_pct = float(values[3])
            results.append(
                {
                    "name": values[0],
                    "code": code,
                    "price": round(float(values[1]), 2),
                    "change": round(float(values[2]), 2),
                    "change_pct": round(change_pct, 2),
                    "up": change_pct >= 0,
                    "high": None,
                    "low": None,
                    "open": None,
                    "prev_close": None,
                    "volume": int(float(values[4])),
                    "amount": float(values[5]),
                }
            )
        if results:
            return {"code": 200, "message": "success (sina fallback)", "data": results}
    except Exception as exc:
        logger.error("请求新浪备用行情失败: %s", exc)
    return _build_fallback(secids)
