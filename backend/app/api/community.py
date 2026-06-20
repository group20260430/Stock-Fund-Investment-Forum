from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session, joinedload

from app.api.posts import _post_payload, _replace_children
from app.core.dependencies import get_current_user, get_optional_current_user
from app.db.session import get_db
from app.models.community import (
    Group,
    GroupMember,
    GroupPost,
    GroupRole,
    GroupVisibility,
    MemberStatus,
    Message,
    MessageType,
)
from app.models.content import Category, Post, PostStatus, PostType
from app.models.user import User, UserStatus
from app.schemas.community import GroupCreate, MemberReview, MessageCreate
from app.schemas.content import PostCreate
from app.schemas.user import ApiResponse

router = APIRouter(tags=["community"])


def _group_or_404(db: Session, group_id: int) -> Group:
    group = db.query(Group).filter(Group.id == group_id).first()
    if group is None:
        raise HTTPException(status_code=404, detail="群组不存在")
    return group


def _membership(db: Session, group_id: int, user_id: int) -> GroupMember | None:
    return db.query(GroupMember).filter(
        GroupMember.group_id == group_id, GroupMember.user_id == user_id
    ).first()


def _group_payload(group: Group, member: GroupMember | None = None) -> dict:
    return {
        "id": group.id,
        "name": group.name,
        "description": group.description,
        "avatar_url": group.avatar_url,
        "visibility": group.visibility.value,
        "need_approval": group.need_approval,
        "creator": {"id": group.creator.id, "nickname": group.creator.nickname},
        "member_count": group.member_count,
        "is_member": bool(member and member.status == MemberStatus.APPROVED),
        "member_status": member.status.value if member else None,
        "member_role": member.role.value if member else None,
        "created_at": group.created_at,
    }


@router.post("/groups", status_code=201)
def create_group(
    data: GroupCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if db.query(Group).filter(Group.name == data.name).first():
        raise HTTPException(status_code=409, detail="群组名称已存在")
    group = Group(
        name=data.name,
        description=data.description,
        avatar_url=data.avatar_url,
        visibility=GroupVisibility(data.visibility),
        need_approval=data.need_approval,
        creator_id=user.id,
        member_count=1,
    )
    db.add(group)
    db.flush()
    db.add(GroupMember(group_id=group.id, user_id=user.id, role=GroupRole.OWNER, status=MemberStatus.APPROVED))
    db.commit()
    return ApiResponse(code=201, message="群组创建成功", data={"id": group.id})


@router.get("/groups")
def list_groups(
    type: str = Query("explore", pattern="^(my|explore|joined)$"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=50),
    user: User | None = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Group).options(joinedload(Group.creator))
    if type in ("my", "joined"):
        if user is None:
            raise HTTPException(status_code=401, detail="请先登录")
        query = query.join(GroupMember).filter(
            GroupMember.user_id == user.id,
            GroupMember.status == MemberStatus.APPROVED,
        )
        if type == "my":
            query = query.filter(GroupMember.role.in_([GroupRole.OWNER, GroupRole.ADMIN]))
    else:
        query = query.filter(Group.visibility == GroupVisibility.PUBLIC)
    total = query.count()
    groups = query.order_by(Group.member_count.desc(), Group.created_at.desc()).offset((page - 1) * size).limit(size).all()
    items = []
    for group in groups:
        member = _membership(db, group.id, user.id) if user else None
        items.append(_group_payload(group, member))
    return ApiResponse(code=200, message="success", data={"items": items, "total": total, "page": page, "size": size})


@router.get("/groups/{group_id}")
def get_group(
    group_id: int,
    user: User | None = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    group = _group_or_404(db, group_id)
    member = _membership(db, group.id, user.id) if user else None
    if group.visibility == GroupVisibility.PRIVATE and not (member and member.status == MemberStatus.APPROVED):
        raise HTTPException(status_code=403, detail="该群组为私密群组")
    return ApiResponse(code=200, message="success", data=_group_payload(group, member))


@router.post("/groups/{group_id}/join")
def join_group(
    group_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    group = _group_or_404(db, group_id)
    member = _membership(db, group_id, user.id)
    if member and member.status == MemberStatus.APPROVED:
        return ApiResponse(code=200, message="已是群组成员", data={"status": "approved"})
    status = MemberStatus.PENDING if group.need_approval else MemberStatus.APPROVED
    if member:
        member.status = status
    else:
        db.add(GroupMember(group_id=group_id, user_id=user.id, status=status))
    if status == MemberStatus.APPROVED:
        group.member_count += 1
    db.commit()
    return ApiResponse(code=200, message="申请已提交" if status == MemberStatus.PENDING else "加入成功", data={"status": status.value})


def _review_member(group_id: int, target_user_id: int, action: str, reviewer: User, db: Session):
    group = _group_or_404(db, group_id)
    reviewer_member = _membership(db, group_id, reviewer.id)
    if reviewer_member is None or reviewer_member.role not in (GroupRole.OWNER, GroupRole.ADMIN):
        raise HTTPException(status_code=403, detail="需要群组管理权限")
    member = _membership(db, group_id, target_user_id)
    if member is None or member.status != MemberStatus.PENDING:
        raise HTTPException(status_code=404, detail="待审核申请不存在")
    member.status = MemberStatus.APPROVED if action == "approve" else MemberStatus.REJECTED
    if member.status == MemberStatus.APPROVED:
        group.member_count += 1
    db.commit()
    return ApiResponse(code=200, message="审核完成", data={"status": member.status.value})


@router.post("/groups/{group_id}/members/approve")
def review_group_member(
    group_id: int,
    data: MemberReview,
    reviewer: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _review_member(group_id, data.user_id, data.action, reviewer, db)


@router.post("/groups/{group_id}/members/{user_id}/approve")
def approve_group_member_compat(
    group_id: int,
    user_id: int,
    reviewer: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _review_member(group_id, user_id, "approve", reviewer, db)


@router.post("/groups/{group_id}/posts", status_code=201)
def create_group_post(
    group_id: int,
    data: PostCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _group_or_404(db, group_id)
    member = _membership(db, group_id, user.id)
    if member is None or member.status != MemberStatus.APPROVED:
        raise HTTPException(status_code=403, detail="只有群组成员可以发帖")
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
    )
    _replace_children(post, data)
    db.add(post)
    db.flush()
    db.add(GroupPost(group_id=group_id, post_id=post.id))
    category.post_count += 1
    db.commit()
    return ApiResponse(code=201, message="群组帖子发布成功", data={"id": post.id})


@router.get("/groups/{group_id}/posts")
def list_group_posts(
    group_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=50),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _group_or_404(db, group_id)
    member = _membership(db, group_id, user.id)
    if member is None or member.status != MemberStatus.APPROVED:
        raise HTTPException(status_code=403, detail="只有群组成员可查看")
    query = db.query(Post).join(GroupPost).options(joinedload(Post.author), joinedload(Post.category)).filter(
        GroupPost.group_id == group_id, Post.status == PostStatus.PUBLISHED
    ).order_by(Post.created_at.desc())
    total = query.count()
    posts = query.offset((page - 1) * size).limit(size).all()
    return ApiResponse(code=200, message="success", data={
        "items": [_post_payload(post, user=user, db=db) for post in posts],
        "total": total, "page": page, "size": size,
    })


def _message_payload(message: Message, current_user_id: int) -> dict:
    other = message.receiver if message.sender_id == current_user_id else message.sender
    return {
        "id": message.id,
        "sender_id": message.sender_id,
        "receiver_id": message.receiver_id,
        "content": message.content,
        "message_type": message.message_type.value,
        "attachment_url": message.attachment_url,
        "is_read": message.is_read,
        "created_at": message.created_at,
        "other_user": {"id": other.id, "nickname": other.nickname, "avatar_url": other.avatar_url},
    }


@router.post("/messages", status_code=201)
def send_message(
    data: MessageCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if data.receiver_id == user.id:
        raise HTTPException(status_code=400, detail="不能给自己发私信")
    receiver = db.query(User).filter(User.id == data.receiver_id, User.status == UserStatus.ACTIVE).first()
    if receiver is None:
        raise HTTPException(status_code=404, detail="接收用户不存在")
    message = Message(
        sender_id=user.id,
        receiver_id=receiver.id,
        content=data.content.strip(),
        message_type=MessageType(data.message_type),
        attachment_url=data.attachment_url,
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return ApiResponse(code=201, message="发送成功", data={"id": message.id})


@router.get("/messages")
def list_messages(
    other_user_id: int | None = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    base = db.query(Message).options(joinedload(Message.sender), joinedload(Message.receiver)).filter(
        or_(Message.sender_id == user.id, Message.receiver_id == user.id)
    )
    if other_user_id is not None:
        base = base.filter(or_(
            and_(Message.sender_id == user.id, Message.receiver_id == other_user_id),
            and_(Message.sender_id == other_user_id, Message.receiver_id == user.id),
        ))
        base.filter(Message.receiver_id == user.id, Message.is_read.is_(False)).update(
            {Message.is_read: True}, synchronize_session=False
        )
        db.commit()
    total = base.count()
    messages = base.order_by(Message.created_at.desc()).offset((page - 1) * size).limit(size).all()
    if other_user_id is None:
        latest: dict[int, Message] = {}
        for message in messages:
            other_id = message.receiver_id if message.sender_id == user.id else message.sender_id
            latest.setdefault(other_id, message)
        messages = list(latest.values())
    return ApiResponse(code=200, message="success", data={
        "items": [_message_payload(item, user.id) for item in messages],
        "total": total, "page": page, "size": size,
    })
