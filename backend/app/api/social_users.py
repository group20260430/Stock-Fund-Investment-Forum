from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_optional_current_user
from app.db.session import get_db
from app.models.content import Post, PostStatus
from app.models.social import Follow, StarredUser
from app.models.user import User, UserStatus
from app.schemas.social import StarredRequest
from app.schemas.user import ApiResponse
from app.api.notifications import create_notification
from app.models.notification import NotificationType
from app.models.operations import ActivityType
from app.services.activity_service import record_activity
from app.services.points_service import award_points

router = APIRouter(tags=["social"])


def _get_privacy(user: User, key: str, default=None):
    """Extract a single privacy setting with fallback to default."""
    settings = user.privacy_settings or {}
    return settings.get(key, default)


def _get_active_user(db: Session, user_id: int) -> User:
    user = db.query(User).filter(User.id == user_id, User.status == UserStatus.ACTIVE).first()
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user


def _user_card(user: User, db: Session, viewer: User | None = None) -> dict:
    is_followed = False
    is_starred = False
    if viewer:
        is_followed = db.query(Follow).filter(
            Follow.follower_id == viewer.id, Follow.following_id == user.id
        ).first() is not None
        is_starred = db.query(StarredUser).filter(
            StarredUser.user_id == viewer.id, StarredUser.starred_user_id == user.id
        ).first() is not None
    return {
        "id": user.id,
        "nickname": user.nickname,
        "avatar_url": user.avatar_url,
        "bio": user.bio,
        "auth_level": user.auth_level.value,
        "is_professional": user.is_professional,
        "followers_count": user.followers_count,
        "following_count": user.following_count,
        "is_followed": is_followed,
        "is_starred": is_starred,
    }


@router.get("/users/{user_id}")
def get_public_profile(
    user_id: int,
    viewer: User | None = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    user = _get_active_user(db, user_id)

    # ── Privacy: profile visibility ──
    profile_visibility = _get_privacy(user, "profile_visibility", "public")
    is_self = viewer is not None and viewer.id == user.id
    if profile_visibility == "private" and not is_self:
        raise HTTPException(status_code=403, detail="该用户设置了私密资料")
    if profile_visibility == "followers_only" and not is_self:
        if viewer is None:
            raise HTTPException(status_code=403, detail="仅粉丝可查看该用户资料")
        is_follower = db.query(Follow).filter(
            Follow.follower_id == viewer.id, Follow.following_id == user.id,
        ).first() is not None
        if not is_follower:
            raise HTTPException(status_code=403, detail="仅粉丝可查看该用户资料")

    post_count = db.query(Post).filter(
        Post.user_id == user.id, Post.status == PostStatus.PUBLISHED
    ).count()
    data = _user_card(user, db, viewer)
    data.update(
        role=user.role.value,
        risk_level=user.risk_level.value if user.risk_level else None,
        investment_tags=user.investment_tags,
        follow_markets=user.follow_markets,
        created_at=user.created_at,
        achievements={
            "posts_count": post_count,
            "elite_posts": db.query(Post).filter(
                Post.user_id == user.id,
                Post.status == PostStatus.PUBLISHED,
                Post.is_elite.is_(True),
            ).count(),
            "influence_score": post_count * 10 + user.followers_count * 5,
            "badges": ["新手入门"] if post_count else [],
        },
        points=user.points or 0,
        level=user.level or 1,
    )

    # ── Privacy: hide investment info from non-owners ──
    if not is_self and not _get_privacy(user, "show_investment_info", True):
        data["risk_level"] = None
        data["investment_tags"] = None
        data["follow_markets"] = None

    return ApiResponse(code=200, message="success", data=data)


@router.post("/users/{user_id}/follow")
def toggle_follow(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    target = _get_active_user(db, user_id)
    if target.id == current_user.id:
        raise HTTPException(status_code=400, detail="不能关注自己")
    existing = db.query(Follow).filter(
        Follow.follower_id == current_user.id, Follow.following_id == target.id
    ).first()
    if existing:
        db.delete(existing)
        current_user.following_count = max(0, current_user.following_count - 1)
        target.followers_count = max(0, target.followers_count - 1)
        followed = False
        record_activity(db, current_user.id, ActivityType.UNFOLLOW, "user", target.id)
    else:
        db.add(Follow(follower_id=current_user.id, following_id=target.id))
        current_user.following_count += 1
        target.followers_count += 1
        followed = True
        record_activity(db, current_user.id, ActivityType.FOLLOW, "user", target.id)
        # ── Points: +1 to followed user ──
        award_points(db, target.id, 1, "gained_follower", "user", current_user.id)
        create_notification(
            db, target.id, NotificationType.FOLLOW,
            title="新关注",
            content=f"{current_user.nickname} 关注了你",
            target_type="user", target_id=current_user.id, sender_id=current_user.id,
        )
    db.commit()
    return ApiResponse(code=200, message="success", data={
        "is_followed": followed,
        "followers_count": target.followers_count,
        "following_count": current_user.following_count,
    })


def _paginate_users(query, page: int, size: int, db: Session, viewer: User | None):
    total = query.count()
    users = query.offset((page - 1) * size).limit(size).all()
    return {
        "items": [_user_card(user, db, viewer) for user in users],
        "total": total,
        "page": page,
        "size": size,
    }


@router.get("/users/{user_id}/followers")
def list_followers(
    user_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=50),
    viewer: User | None = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    user = _get_active_user(db, user_id)
    # ── Privacy: show_follow_lists ──
    is_self = viewer is not None and viewer.id == user.id
    if not is_self and not _get_privacy(user, "show_follow_lists", True):
        raise HTTPException(status_code=403, detail="该用户未公开关注列表")
    query = db.query(User).join(Follow, Follow.follower_id == User.id).filter(
        Follow.following_id == user_id, User.status == UserStatus.ACTIVE
    ).order_by(Follow.created_at.desc())
    return ApiResponse(code=200, message="success", data=_paginate_users(query, page, size, db, viewer))


@router.get("/users/{user_id}/following")
def list_following(
    user_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=50),
    viewer: User | None = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    user = _get_active_user(db, user_id)
    # ── Privacy: show_follow_lists ──
    is_self = viewer is not None and viewer.id == user.id
    if not is_self and not _get_privacy(user, "show_follow_lists", True):
        raise HTTPException(status_code=403, detail="该用户未公开关注列表")
    query = db.query(User).join(Follow, Follow.following_id == User.id).filter(
        Follow.follower_id == user_id, User.status == UserStatus.ACTIVE
    ).order_by(Follow.created_at.desc())
    return ApiResponse(code=200, message="success", data=_paginate_users(query, page, size, db, viewer))


@router.put("/users/me/starred")
def set_starred(
    data: StarredRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    target = _get_active_user(db, data.user_id)
    if target.id == current_user.id:
        raise HTTPException(status_code=400, detail="不能星标自己")
    existing = db.query(StarredUser).filter(
        StarredUser.user_id == current_user.id, StarredUser.starred_user_id == target.id
    ).first()
    if data.is_starred and existing is None:
        db.add(StarredUser(user_id=current_user.id, starred_user_id=target.id))
    elif not data.is_starred and existing is not None:
        db.delete(existing)
    db.commit()
    return ApiResponse(code=200, message="success", data={"is_starred": data.is_starred})


@router.get("/users/{user_id}/points")
def get_user_points(
    user_id: int,
    db: Session = Depends(get_db),
):
    """获取用户的积分和等级信息（公开接口）。"""
    user = _get_active_user(db, user_id)
    return ApiResponse(code=200, message="success", data={
        "user_id": user.id,
        "nickname": user.nickname,
        "points": user.points or 0,
        "level": user.level or 1,
    })
