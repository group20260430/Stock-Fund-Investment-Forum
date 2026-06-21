from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session, joinedload

from app.api.posts import _get_post_or_404, _post_payload
from app.core.dependencies import get_current_user, get_optional_current_user
from app.db.session import get_db
from app.models.content import (
    Comment,
    CommentStatus,
    Favorite,
    FavoriteFolder,
    Like,
    LikeTarget,
    Post,
    Share,
    ShareType,
)
from app.models.user import User, UserRole
from app.schemas.interactions import CollectRequest, CommentCreate, ShareRequest
from app.schemas.user import ApiResponse
from app.models.operations import ActivityType
from app.services.activity_service import record_activity
from app.services.sensitive_word_service import check_sensitive_texts

router = APIRouter(tags=["interactions"])


def _comment_payload(comment: Comment, liked_ids: set[int], reply_author: User | None = None) -> dict:
    return {
        "id": comment.id,
        "content": comment.content,
        "author": {
            "id": comment.author.id,
            "nickname": comment.author.nickname,
            "avatar_url": comment.author.avatar_url,
        },
        "reply_to": (
            {"id": reply_author.id, "nickname": reply_author.nickname}
            if reply_author else None
        ),
        "like_count": comment.like_count,
        "is_liked": comment.id in liked_ids,
        "created_at": comment.created_at,
        "replies": [],
    }


@router.get("/posts/{post_id}/comments")
def list_comments(
    post_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=50),
    user: User | None = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    _get_post_or_404(db, post_id)
    base = db.query(Comment).options(joinedload(Comment.author)).filter(
        Comment.post_id == post_id,
        Comment.status == CommentStatus.PUBLISHED,
    )
    roots_query = base.filter(Comment.parent_id.is_(None)).order_by(Comment.created_at.desc())
    total = roots_query.count()
    roots = roots_query.offset((page - 1) * size).limit(size).all()
    root_ids = [item.id for item in roots]
    replies = (
        base.filter(Comment.parent_id.in_(root_ids)).order_by(Comment.created_at.asc()).all()
        if root_ids else []
    )
    all_ids = [item.id for item in roots + replies]
    liked_ids: set[int] = set()
    if user and all_ids:
        liked_ids = {
            item.target_id for item in db.query(Like).filter(
                Like.user_id == user.id,
                Like.target_type == LikeTarget.COMMENT,
                Like.target_id.in_(all_ids),
            ).all()
        }
    author_ids = {item.reply_to.user_id for item in replies if item.reply_to is not None}
    authors = {item.id: item for item in db.query(User).filter(User.id.in_(author_ids)).all()} if author_ids else {}
    payloads = {item.id: _comment_payload(item, liked_ids) for item in roots}
    for reply in replies:
        reply_author = authors.get(reply.reply_to.user_id) if reply.reply_to else None
        payloads[reply.parent_id]["replies"].append(_comment_payload(reply, liked_ids, reply_author))
    return ApiResponse(code=200, message="success", data={
        "items": list(payloads.values()), "total": total, "page": page, "size": size
    })


@router.post("/posts/{post_id}/comments", status_code=201)
def create_comment(
    post_id: int,
    data: CommentCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    post = _get_post_or_404(db, post_id)
    parent = None
    if data.parent_id is not None:
        parent = db.query(Comment).filter(Comment.id == data.parent_id, Comment.post_id == post_id).first()
        if parent is None:
            raise HTTPException(status_code=400, detail="父评论不存在")
        if parent.parent_id is not None:
            parent = db.query(Comment).filter(Comment.id == parent.parent_id).first()
    if data.reply_to_id is not None:
        reply_to = db.query(Comment).filter(Comment.id == data.reply_to_id, Comment.post_id == post_id).first()
        if reply_to is None:
            raise HTTPException(status_code=400, detail="被回复评论不存在")
    sensitive_result = check_sensitive_texts(db, [data.content])
    if sensitive_result.should_block:
        raise HTTPException(status_code=400, detail="内容包含禁止发布的敏感词")
    comment = Comment(
        post_id=post_id,
        user_id=user.id,
        parent_id=parent.id if parent else None,
        reply_to_id=data.reply_to_id,
        content=data.content.strip(),
        status=CommentStatus.REVIEWING if sensitive_result.should_review else CommentStatus.PUBLISHED,
    )
    db.add(comment)
    db.flush()
    record_activity(db, user.id, ActivityType.COMMENT, "comment", comment.id)
    post.comment_count += 1
    db.commit()
    return ApiResponse(code=201, message="评论成功", data={"id": comment.id})


@router.delete("/comments/{comment_id}", status_code=204)
def delete_comment(
    comment_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if comment is None:
        raise HTTPException(status_code=404, detail="评论不存在")
    if comment.user_id != user.id and user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="无权删除该评论")
    post = db.query(Post).filter(Post.id == comment.post_id).first()
    child_count = db.query(Comment).filter(Comment.parent_id == comment.id).count()
    db.delete(comment)
    if post:
        post.comment_count = max(0, post.comment_count - child_count - 1)
    db.commit()
    return Response(status_code=204)


@router.post("/comments/{comment_id}/like")
def toggle_comment_like(
    comment_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if comment is None:
        raise HTTPException(status_code=404, detail="评论不存在")
    existing = db.query(Like).filter(
        Like.user_id == user.id, Like.target_type == LikeTarget.COMMENT, Like.target_id == comment_id
    ).first()
    if existing:
        db.delete(existing)
        comment.like_count = max(0, comment.like_count - 1)
        liked = False
    else:
        db.add(Like(user_id=user.id, target_type=LikeTarget.COMMENT, target_id=comment_id))
        comment.like_count += 1
        liked = True
        record_activity(db, user.id, ActivityType.LIKE, "comment", comment_id)
    db.commit()
    return ApiResponse(code=200, message="success", data={"is_liked": liked, "like_count": comment.like_count})


@router.post("/posts/{post_id}/like")
def toggle_post_like(
    post_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    post = _get_post_or_404(db, post_id)
    existing = db.query(Like).filter(
        Like.user_id == user.id, Like.target_type == LikeTarget.POST, Like.target_id == post_id
    ).first()
    if existing:
        db.delete(existing)
        post.like_count = max(0, post.like_count - 1)
        liked = False
    else:
        db.add(Like(user_id=user.id, target_type=LikeTarget.POST, target_id=post_id))
        post.like_count += 1
        liked = True
        record_activity(db, user.id, ActivityType.LIKE, "post", post_id)
    db.commit()
    return ApiResponse(code=200, message="success", data={"is_liked": liked, "like_count": post.like_count})


@router.post("/posts/{post_id}/collect")
def toggle_collect(
    post_id: int,
    data: CollectRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    post = _get_post_or_404(db, post_id)
    existing = db.query(Favorite).filter(Favorite.user_id == user.id, Favorite.post_id == post_id).first()
    if existing:
        db.delete(existing)
        post.collect_count = max(0, post.collect_count - 1)
        collected = False
    else:
        folder = db.query(FavoriteFolder).filter(
            FavoriteFolder.user_id == user.id, FavoriteFolder.name == data.folder_name
        ).first()
        if folder is None:
            folder = FavoriteFolder(user_id=user.id, name=data.folder_name)
            db.add(folder)
            db.flush()
        db.add(Favorite(user_id=user.id, post_id=post_id, folder_id=folder.id))
        post.collect_count += 1
        collected = True
    db.commit()
    return ApiResponse(code=200, message="success", data={"is_collected": collected, "collect_count": post.collect_count})


@router.get("/users/me/collections")
def list_collections(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=50),
    folder_name: str | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Favorite).options(
        joinedload(Favorite.post).joinedload(Post.author),
        joinedload(Favorite.post).joinedload(Post.category),
        joinedload(Favorite.folder),
    ).filter(Favorite.user_id == user.id)
    if folder_name:
        query = query.join(FavoriteFolder).filter(FavoriteFolder.name == folder_name)
    total = query.count()
    favorites = query.order_by(Favorite.created_at.desc()).offset((page - 1) * size).limit(size).all()
    return ApiResponse(code=200, message="success", data={
        "items": [dict(_post_payload(item.post), folder_name=item.folder.name, collected_at=item.created_at) for item in favorites],
        "total": total, "page": page, "size": size,
    })


@router.post("/posts/{post_id}/share", status_code=201)
def share_post(
    post_id: int,
    data: ShareRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    post = _get_post_or_404(db, post_id)
    share = Share(user_id=user.id, post_id=post_id, share_type=ShareType(data.share_type), comment=data.comment)
    db.add(share)
    db.flush()
    record_activity(db, user.id, ActivityType.SHARE, "post", post_id)
    post.share_count += 1
    db.commit()
    return ApiResponse(code=201, message="分享成功", data={"id": share.id, "share_count": post.share_count})
