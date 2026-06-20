from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_optional_current_user
from app.db.session import get_db
from app.models.content import Post, PostStatus
from app.models.social import Follow, StarredUser
from app.models.user import User, UserStatus
from app.schemas.social import StarredRequest
from app.schemas.user import ApiResponse

router = APIRouter(tags=["social"])


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
    )
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
    else:
        db.add(Follow(follower_id=current_user.id, following_id=target.id))
        current_user.following_count += 1
        target.followers_count += 1
        followed = True
    db.commit()
    return ApiResponse(code=200, message="success", data={
        "is_followed": followed, "followers_count": target.followers_count
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
    _get_active_user(db, user_id)
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
    _get_active_user(db, user_id)
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
