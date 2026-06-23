from collections import Counter
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.api.posts import _post_payload
from app.api.social_users import _user_card
from app.core.dependencies import get_current_user, get_optional_current_user
from app.db.session import get_db
from app.models.community import Group, GroupMember, GroupVisibility, MemberStatus
from app.models.content import Post, PostStatus, Share
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


def _group_card(group: Group, viewer: User | None, db: Session) -> dict:
    member = None
    if viewer:
        member = db.query(GroupMember).filter(
            GroupMember.group_id == group.id,
            GroupMember.user_id == viewer.id,
        ).first()
    return {
        "id": group.id,
        "name": group.name,
        "description": group.description,
        "avatar_url": group.avatar_url,
        "visibility": group.visibility.value,
        "member_count": group.member_count,
        "is_member": bool(member and member.status == MemberStatus.APPROVED),
        "member_status": member.status.value if member else None,
        "result_type": "group",
    }


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
    # 关注的人的帖子
    followed_posts = _base_posts(db).filter(Post.user_id.in_(author_ids)).all()
    followed_post_ids = {p.id for p in followed_posts}
    # 关注的人分享过的、且不在上述帖子列表中的帖子
    shared_post_ids = {
        s.post_id for s in db.query(Share).filter(Share.user_id.in_(author_ids)).all()
        if s.post_id not in followed_post_ids
    }
    shared_posts = _base_posts(db).filter(Post.id.in_(shared_post_ids)).all() if shared_post_ids else []
    # 合并并按时间排序
    all_posts = followed_posts + shared_posts
    all_posts.sort(key=lambda p: p.created_at or datetime.min, reverse=True)
    total = len(all_posts)
    page_posts = all_posts[(page - 1) * size: page * size]
    payloads = []
    for post in page_posts:
        pdata = _post_payload(post, user=user, db=db)
        # 标记是否来自他人分享
        share = db.query(Share).filter(
            Share.post_id == post.id, Share.user_id.in_(author_ids)
        ).order_by(Share.created_at.desc()).first()
        if share:
            if share.user_id == user.id:
                pdata["shared_by"] = "__self__"
            else:
                sharer = db.query(User).filter(User.id == share.user_id).first()
                pdata["shared_by"] = sharer.nickname if sharer else None
        payloads.append(pdata)
    return ApiResponse(code=200, message="success", data={
        "items": payloads,
        "total": total, "page": page, "size": size,
    })


@router.get("/hot")
def hot_ranking(
    period: str = Query("daily", pattern="^(daily|weekly|monthly)$"),
    market: str = Query("all", pattern="^(all|a_stock|hk_stock|fund)$"),
    db: Session = Depends(get_db),
):
    periods = ["daily", "weekly", "monthly"]
    # 按顺序尝试：daily -> weekly -> monthly -> 全部，直到有结果
    start_idx = periods.index(period)
    top_posts = []
    for i in range(start_idx, len(periods) + 1):
        if i < len(periods):
            cutoff = _cutoff(periods[i])
            top_posts = (
                _base_posts(db)
                .filter(Post.created_at >= cutoff)
                .order_by(
                    (Post.view_count + Post.like_count * 5 + Post.comment_count * 8 + Post.collect_count * 4).desc()
                )
                .limit(200)
                .all()
            )
        else:
            # 最后一次尝试：不限时间
            top_posts = (
                _base_posts(db)
                .order_by(
                    (Post.view_count + Post.like_count * 5 + Post.comment_count * 8 + Post.collect_count * 4).desc()
                )
                .limit(200)
                .all()
            )
        if top_posts:
            break
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
    type: str = Query("all", pattern="^(all|post|user|stock|group)$"),
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
    elif type == "group":
        query = db.query(Group).filter(
            Group.visibility == GroupVisibility.PUBLIC,
            or_(Group.name.ilike(pattern), Group.description.ilike(pattern)),
        )
        total = query.count()
        groups = query.order_by(Group.member_count.desc(), Group.created_at.desc()).offset((page - 1) * size).limit(size).all()
        items = [_group_card(group, viewer, db) for group in groups]
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
        users = db.query(User).filter(
            User.status == UserStatus.ACTIVE,
            or_(User.nickname.ilike(pattern), User.bio.ilike(pattern)),
        ).order_by(User.followers_count.desc()).limit(3).all()
        stocks = [item for item in SECURITIES if term.lower() in item["code"].lower() or term.lower() in item["name"].lower()][:3]
        groups = db.query(Group).filter(
            Group.visibility == GroupVisibility.PUBLIC,
            or_(Group.name.ilike(pattern), Group.description.ilike(pattern)),
        ).order_by(Group.member_count.desc(), Group.created_at.desc()).limit(3).all()
        items.extend(dict(_user_card(user, db, viewer), result_type="user") for user in users)
        items.extend(dict(item, result_type="stock") for item in stocks)
        items.extend(_group_card(group, viewer, db) for group in groups)
        total += len(users) + len(stocks) + len(groups)
    return ApiResponse(code=200, message="success", data={"items": items, "total": total, "page": page, "size": size})


@router.get("/search/recommendations")
def search_recommendations(
    viewer: User | None = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    posts = (
        _base_posts(db)
        .order_by((Post.view_count + Post.like_count * 5 + Post.comment_count * 8).desc(), Post.created_at.desc())
        .limit(3)
        .all()
    )
    users = (
        db.query(User)
        .filter(User.status == UserStatus.ACTIVE)
        .order_by(User.followers_count.desc(), User.created_at.desc())
        .limit(3)
        .all()
    )
    return ApiResponse(code=200, message="success", data={
        "posts": [dict(_post_payload(post, user=viewer, db=db), result_type="post") for post in posts],
        "users": [dict(_user_card(user, db, viewer), result_type="user") for user in users],
        "stocks": [dict(item, result_type="stock") for item in SECURITIES[:3]],
    })


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
