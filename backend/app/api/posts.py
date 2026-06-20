from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.content import Attachment, Category, Post, PostStatus, PostType, VoteOption, VoteRecord
from app.models.user import User, UserRole
from app.schemas.content import PostCreate, PostUpdate, VoteRequest
from app.schemas.user import ApiResponse

router = APIRouter(tags=["posts"])


def _author_payload(user: User) -> dict:
    return {
        "id": user.id,
        "nickname": user.nickname,
        "avatar_url": user.avatar_url,
        "auth_level": user.auth_level.value,
    }


def _post_payload(post: Post, detail: bool = False) -> dict:
    data = {
        "id": post.id,
        "title": post.title,
        "content_summary": post.content[:160],
        "author": _author_payload(post.author),
        "category": {"id": post.category.id, "name": post.category.name},
        "post_type": post.post_type.value,
        "status": post.status.value,
        "view_count": post.view_count,
        "like_count": post.like_count,
        "comment_count": post.comment_count,
        "collect_count": post.collect_count,
        "share_count": post.share_count,
        "is_elite": post.is_elite,
        "is_liked": False,
        "is_collected": False,
        "tags": post.tags or [],
        "created_at": post.created_at,
        "updated_at": post.updated_at,
    }
    if detail:
        data.update(
            content=post.content,
            attachments=[
                {
                    "id": item.id,
                    "file_name": item.file_name,
                    "file_url": item.file_url,
                    "file_size": item.file_size,
                    "file_type": item.file_type,
                }
                for item in post.attachments
            ],
            vote_options=[
                {"id": item.id, "label": item.label, "vote_count": item.vote_count}
                for item in post.vote_options
            ],
        )
    return data


def _post_query(db: Session):
    return db.query(Post).options(
        joinedload(Post.author),
        joinedload(Post.category),
        joinedload(Post.attachments),
        joinedload(Post.vote_options),
    )


def _get_post_or_404(db: Session, post_id: int) -> Post:
    post = _post_query(db).filter(Post.id == post_id).first()
    if post is None:
        raise HTTPException(status_code=404, detail="帖子不存在")
    return post


def _ensure_owner_or_admin(post: Post, user: User) -> None:
    if post.user_id != user.id and user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="无权修改该帖子")


def _replace_children(post: Post, data: PostCreate) -> None:
    post.attachments.clear()
    post.vote_options.clear()
    for item in data.attachments:
        post.attachments.append(Attachment(**item.model_dump()))
    if data.post_type == "poll":
        for index, item in enumerate(data.vote_options):
            post.vote_options.append(VoteOption(label=item.label, sort_order=index))


@router.get("/categories")
def list_categories(db: Session = Depends(get_db)):
    categories = db.query(Category).filter(Category.is_active.is_(True)).order_by(Category.sort_order, Category.id).all()
    return ApiResponse(
        code=200,
        message="success",
        data=[
            {
                "id": item.id,
                "name": item.name,
                "description": item.description,
                "sort_order": item.sort_order,
                "post_count": item.post_count,
            }
            for item in categories
        ],
    )


@router.get("/posts")
def list_posts(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=50),
    sort: str = Query("latest", pattern="^(latest|hot|elite)$"),
    category_id: int | None = None,
    keyword: str | None = Query(None, max_length=100),
    db: Session = Depends(get_db),
):
    query = _post_query(db).filter(Post.status == PostStatus.PUBLISHED)
    if category_id is not None:
        query = query.filter(Post.category_id == category_id)
    if keyword:
        term = f"%{keyword.strip()}%"
        query = query.filter(or_(Post.title.ilike(term), Post.content.ilike(term)))
    if sort == "hot":
        query = query.order_by((Post.like_count + Post.comment_count + Post.view_count).desc())
    elif sort == "elite":
        query = query.filter(Post.is_elite.is_(True)).order_by(Post.created_at.desc())
    else:
        query = query.order_by(Post.created_at.desc())
    total = query.count()
    posts = query.offset((page - 1) * size).limit(size).all()
    return ApiResponse(code=200, message="success", data={
        "items": [_post_payload(post) for post in posts],
        "total": total,
        "page": page,
        "size": size,
    })


@router.post("/posts", status_code=201)
def create_post(data: PostCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    category = db.query(Category).filter(Category.id == data.category_id, Category.is_active.is_(True)).first()
    if category is None:
        raise HTTPException(status_code=404, detail="板块不存在")
    post = Post(
        user_id=user.id,
        category_id=data.category_id,
        title=data.title,
        content=data.content,
        post_type=PostType(data.post_type),
        status=PostStatus(data.status),
        tags=data.tags,
        last_activity_at=datetime.now(timezone.utc),
    )
    _replace_children(post, data)
    db.add(post)
    category.post_count += 1
    db.commit()
    return ApiResponse(code=201, message="发布成功", data={"id": post.id})


@router.get("/posts/{post_id}")
def get_post(post_id: int, db: Session = Depends(get_db)):
    post = _get_post_or_404(db, post_id)
    if post.status != PostStatus.PUBLISHED:
        raise HTTPException(status_code=404, detail="帖子不存在")
    post.view_count += 1
    db.commit()
    db.refresh(post)
    return ApiResponse(code=200, message="success", data=_post_payload(post, detail=True))


@router.put("/posts/{post_id}")
def update_post(
    post_id: int,
    data: PostUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    post = _get_post_or_404(db, post_id)
    _ensure_owner_or_admin(post, user)
    category = db.query(Category).filter(Category.id == data.category_id, Category.is_active.is_(True)).first()
    if category is None:
        raise HTTPException(status_code=404, detail="板块不存在")
    if post.category_id != data.category_id:
        post.category.post_count = max(0, post.category.post_count - 1)
        category.post_count += 1
    post.category_id = data.category_id
    post.title = data.title
    post.content = data.content
    post.post_type = PostType(data.post_type)
    post.status = PostStatus(data.status)
    post.tags = data.tags
    post.last_activity_at = datetime.now(timezone.utc)
    _replace_children(post, data)
    db.commit()
    return ApiResponse(code=200, message="编辑成功", data={"id": post.id})


@router.delete("/posts/{post_id}", status_code=204)
def delete_post(
    post_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    post = _get_post_or_404(db, post_id)
    _ensure_owner_or_admin(post, user)
    category = post.category
    db.delete(post)
    category.post_count = max(0, category.post_count - 1)
    db.commit()
    return Response(status_code=204)


@router.post("/posts/{post_id}/vote")
def vote_post(
    post_id: int,
    data: VoteRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    post = _get_post_or_404(db, post_id)
    if post.post_type != PostType.POLL:
        raise HTTPException(status_code=400, detail="该帖子不是投票帖")
    option_ids = set(data.option_ids)
    valid_options = [item for item in post.vote_options if item.id in option_ids]
    if len(valid_options) != len(option_ids):
        raise HTTPException(status_code=400, detail="包含无效的投票选项")

    old_records = db.query(VoteRecord).filter(
        VoteRecord.user_id == user.id, VoteRecord.post_id == post.id
    ).all()
    old_option_ids = {item.option_id for item in old_records}
    for option in post.vote_options:
        if option.id in old_option_ids:
            option.vote_count = max(0, option.vote_count - 1)
    for record in old_records:
        db.delete(record)
    for option in valid_options:
        option.vote_count += 1
        db.add(VoteRecord(user_id=user.id, post_id=post.id, option_id=option.id))
    db.commit()
    return ApiResponse(code=200, message="投票成功", data={
        "results": [
            {"option_id": item.id, "label": item.label, "vote_count": item.vote_count}
            for item in post.vote_options
        ]
    })
