from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.schemas.user import ApiResponse

router = APIRouter(prefix="/posts", tags=["posts"])

# 模拟帖子数据 — 字段名与前端 PostCard 对齐
MOCK_POSTS = [
    {
        "id": 1,
        "title": "A股市场今日讨论",
        "author": "系统用户",
        "category": "股票",
        "content_summary": "今天大盘走势回顾，沪指震荡上行，成交量有所放大，市场情绪回暖。板块方面，新能源、半导体表现活跃。",
        "like_count": 12,
        "comment_count": 3,
        "collect_count": 2,
        "share_count": 1,
        "view_count": 256,
        "is_elite": False,
        "is_liked": False,
        "is_collected": False,
        "tags": ["A股", "大盘分析"],
        "post_type": "normal",
        "created_at": "2026-06-18T10:00:00Z",
    },
    {
        "id": 2,
        "title": "指数基金长期配置思路",
        "author": "基金观察员",
        "category": "基金",
        "content_summary": "在当前市场环境下，宽基指数基金依然是长期配置的首选。建议关注沪深300和中证500的定投机会。",
        "like_count": 21,
        "comment_count": 7,
        "collect_count": 5,
        "share_count": 3,
        "view_count": 412,
        "is_elite": True,
        "is_liked": False,
        "is_collected": False,
        "tags": ["指数基金", "定投", "配置"],
        "post_type": "long_article",
        "created_at": "2026-06-17T14:30:00Z",
    },
    {
        "id": 3,
        "title": "新手该怎么选基金？",
        "author": "理财小白",
        "category": "问答求助",
        "content_summary": "刚工作一年，想开始理财，请问各位大佬有什么适合新手的基金推荐吗？",
        "like_count": 8,
        "comment_count": 15,
        "collect_count": 10,
        "share_count": 0,
        "view_count": 890,
        "is_elite": False,
        "is_liked": False,
        "is_collected": False,
        "tags": ["新手", "基金入门"],
        "post_type": "normal",
        "created_at": "2026-06-16T09:15:00Z",
    },
    {
        "id": 4,
        "title": "2026下半年投资策略展望",
        "author": "策略分析师",
        "category": "投资策略",
        "content_summary": "从宏观经济数据和市场估值水平来看，下半年A股有望迎来修复行情，重点关注消费复苏和科技创新两条主线。",
        "like_count": 35,
        "comment_count": 12,
        "collect_count": 18,
        "share_count": 6,
        "view_count": 1200,
        "is_elite": True,
        "is_liked": False,
        "is_collected": False,
        "tags": ["投资策略", "展望", "A股"],
        "post_type": "long_article",
        "created_at": "2026-06-15T16:00:00Z",
    },
    {
        "id": 5,
        "title": "港股通标的分析：腾讯VS阿里",
        "author": "港股猎手",
        "category": "股票市场",
        "content_summary": "对比分析腾讯和阿里当前估值、业务增长点和投资价值，供大家参考。",
        "like_count": 18,
        "comment_count": 9,
        "collect_count": 7,
        "share_count": 4,
        "view_count": 567,
        "is_elite": False,
        "is_liked": False,
        "is_collected": False,
        "tags": ["港股", "腾讯", "阿里"],
        "post_type": "normal",
        "created_at": "2026-06-14T11:20:00Z",
    },
]


@router.get("")
def list_posts(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=50),
    sort: Optional[str] = Query(None),
    category_id: Optional[int] = Query(None),
    keyword: Optional[str] = Query(None),
):
    """获取帖子列表 — 返回分页数据，字段名与前端 PostCard 对齐。"""
    items = MOCK_POSTS

    # 按分类筛选
    if category_id is not None:
        category_map = {1: "综合讨论", 2: "股票市场", 3: "基金", 4: "问答求助", 5: "投资策略"}
        cat_name = category_map.get(category_id)
        if cat_name:
            items = [p for p in items if p["category"] == cat_name]

    # 关键词搜索
    if keyword:
        keyword_lower = keyword.lower()
        items = [
            p
            for p in items
            if keyword_lower in p["title"].lower() or keyword_lower in p["content_summary"].lower()
        ]

    # 排序
    if sort == "hot":
        items = sorted(items, key=lambda p: p["like_count"] + p["comment_count"], reverse=True)
    elif sort == "elite":
        items = [p for p in items if p["is_elite"]]
    else:
        items = sorted(items, key=lambda p: p["created_at"], reverse=True)

    total = len(items)
    start = (page - 1) * size
    end = start + size
    page_items = items[start:end] if start < total else []

    return ApiResponse(
        code=200,
        message="success",
        data={
            "items": page_items,
            "total": total,
            "page": page,
            "size": size,
        },
    )
