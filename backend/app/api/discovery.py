from collections import Counter
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.api.posts import _post_payload
from app.api.social_users import _user_card
from app.core.dependencies import get_current_user, get_optional_current_user
from app.db.session import get_db
from app.models.content import Post, PostStatus
from app.models.social import Follow, StarredUser
from app.models.user import User, UserStatus
from app.schemas.user import ApiResponse

router = APIRouter(tags=["discovery"])

SECURITIES = [
    {"code": "000001", "name": "上证指数", "market": "A股"},
    {"code": "000300", "name": "沪深300", "market": "A股"},
    {"code": "399001", "name": "深证成指", "market": "A股"},
    {"code": "000905", "name": "中证500", "market": "A股"},
]


def _base_posts(db: Session):
    return db.query(Post).options(joinedload(Post.author), joinedload(Post.category)).filter(
        Post.status == PostStatus.PUBLISHED
    )


def _cutoff(period: str) -> datetime:
    days = {"daily": 1, "weekly": 7, "monthly": 30}[period]
    return datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days)


@router.get("/feed")
def personalized_feed(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=50),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    followed_ids = {
        item.following_id for item in db.query(Follow).filter(Follow.follower_id == user.id).all()
    }
    starred_ids = {
        item.starred_user_id for item in db.query(StarredUser).filter(StarredUser.user_id == user.id).all()
    }
    author_ids = followed_ids | starred_ids | {user.id}
    query = _base_posts(db).filter(Post.user_id.in_(author_ids))
    if query.count() == 0:
        query = _base_posts(db)
    total = query.count()
    posts = query.order_by(Post.created_at.desc()).offset((page - 1) * size).limit(size).all()
    return ApiResponse(code=200, message="success", data={
        "items": [_post_payload(post, user=user, db=db) for post in posts],
        "total": total, "page": page, "size": size,
    })


@router.get("/hot")
def hot_ranking(
    period: str = Query("daily", pattern="^(daily|weekly|monthly)$"),
    market: str = Query("all", pattern="^(all|a_stock|hk_stock|fund)$"),
    db: Session = Depends(get_db),
):
    cutoff = _cutoff(period)
    # 只取热度最高的前200篇帖子做聚合，防止全表扫描
    top_posts = (
        _base_posts(db)
        .filter(Post.created_at >= cutoff)
        .order_by(
            (Post.view_count + Post.like_count * 5 + Post.comment_count * 8 + Post.collect_count * 4).desc()
        )
        .limit(200)
        .all()
    )
    tag_stats: dict[str, dict] = {}
    for post in top_posts:
        tags = post.tags or [post.category.name]
        score = post.view_count + post.like_count * 5 + post.comment_count * 8 + post.collect_count * 4
        for tag in tags:
            item = tag_stats.setdefault(tag, {"discussion_count": 0, "heat_score": 0, "post_ids": []})
            item["discussion_count"] += 1
            item["heat_score"] += score
            item["post_ids"].append(post.id)
    ranked = sorted(tag_stats.items(), key=lambda pair: pair[1]["heat_score"], reverse=True)[:20]
    data = [dict(topic=topic, rank=index + 1, **stats) for index, (topic, stats) in enumerate(ranked)]
    return ApiResponse(code=200, message="success", data=data)


@router.get("/search")
def search(
    keyword: str = Query(..., min_length=1, max_length=100),
    type: str = Query("all", pattern="^(all|post|user|stock)$"),
    category_id: int | None = None,
    time_range: str = Query("all", pattern="^(all|day|week|month)$"),
    sort: str = Query("relevance", pattern="^(relevance|time|heat)$"),
    is_elite: bool | None = None,
    market: str | None = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=50),
    viewer: User | None = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    term = keyword.strip()
    pattern = f"%{term}%"
    if type == "user":
        query = db.query(User).filter(
            User.status == UserStatus.ACTIVE,
            or_(User.nickname.ilike(pattern), User.bio.ilike(pattern)),
        )
        total = query.count()
        users = query.offset((page - 1) * size).limit(size).all()
        items = [
            dict(_user_card(user, db, viewer), result_type="user")
            for user in users
        ]
    elif type == "stock":
        matches = [item for item in SECURITIES if term.lower() in item["code"].lower() or term.lower() in item["name"].lower()]
        total = len(matches)
        items = [dict(item, result_type="stock") for item in matches[(page - 1) * size:page * size]]
    else:
        query = _base_posts(db).filter(or_(Post.title.ilike(pattern), Post.content.ilike(pattern)))
        if category_id is not None:
            query = query.filter(Post.category_id == category_id)
        if is_elite is not None:
            query = query.filter(Post.is_elite == is_elite)
        if time_range != "all":
            days = {"day": 1, "week": 7, "month": 30}[time_range]
            query = query.filter(Post.created_at >= datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days))
        if sort == "time":
            query = query.order_by(Post.created_at.desc())
        elif sort == "heat":
            query = query.order_by((Post.view_count + Post.like_count * 5 + Post.comment_count * 8).desc())
        else:
            query = query.order_by(Post.is_elite.desc(), Post.created_at.desc())
        total = query.count()
        posts = query.offset((page - 1) * size).limit(size).all()
        items = [dict(_post_payload(post, user=viewer, db=db), result_type="post") for post in posts]
    return ApiResponse(code=200, message="success", data={"items": items, "total": total, "page": page, "size": size})


@router.get("/search/suggestions")
def search_suggestions(
    keyword: str = Query(..., min_length=1, max_length=100),
    type: str = Query("all", pattern="^(all|stock|user|topic)$"),
    db: Session = Depends(get_db),
):
    term = keyword.strip().lower()
    stocks = [item for item in SECURITIES if term in item["code"].lower() or term in item["name"].lower()][:5]
    users = db.query(User).filter(
        User.status == UserStatus.ACTIVE, User.nickname.ilike(f"%{keyword.strip()}%")
    ).limit(5).all()
    tag_counter = Counter()
    for tags, in db.query(Post.tags).filter(Post.status == PostStatus.PUBLISHED).all():
        for tag in tags or []:
            if term in tag.lower():
                tag_counter[tag] += 1
    return ApiResponse(code=200, message="success", data={
        "stocks": stocks if type in ("all", "stock") else [],
        "users": [
            {"id": user.id, "nickname": user.nickname, "avatar_url": user.avatar_url}
            for user in users
        ] if type in ("all", "user") else [],
        "topics": [tag for tag, _ in tag_counter.most_common(5)] if type in ("all", "topic") else [],
    })
