from fastapi import APIRouter

router = APIRouter(prefix="/posts", tags=["posts"])


@router.get("")
def list_posts() -> list[dict[str, object]]:
    return [
        {
            "id": 1,
            "title": "A股市场今日讨论",
            "author": "系统用户",
            "category": "股票",
            "summary": "这里是论坛帖子列表接口的示例数据。",
            "likes": 12,
            "comments": 3,
        },
        {
            "id": 2,
            "title": "指数基金长期配置思路",
            "author": "基金观察员",
            "category": "基金",
            "summary": "后续可替换为 MySQL 查询结果。",
            "likes": 21,
            "comments": 7,
        },
    ]
