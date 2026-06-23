from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session, joinedload

from app.api.notifications import create_notification
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
from app.models.notification import NotificationType
from app.models.social import Follow
from app.models.user import User, UserStatus
from app.schemas.community import GroupCreate, GroupPostCreate, GroupUpdate, MemberReview, MessageCreate
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
    elif status == MemberStatus.PENDING:
        create_notification(
            db, group.creator_id, NotificationType.GROUP_JOIN_REQUEST,
            title="新的加群申请",
            content=f"{user.nickname} 申请加入 {group.name}",
            target_type="group", target_id=group.id, sender_id=user.id,
        )
    db.commit()
    return ApiResponse(code=200, message="申请已提交" if status == MemberStatus.PENDING else "加入成功", data={"status": status.value})


@router.post("/groups/{group_id}/leave")
def leave_group(
    group_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    group = _group_or_404(db, group_id)
    member = _membership(db, group_id, user.id)
    if member is None or member.status != MemberStatus.APPROVED:
        raise HTTPException(status_code=400, detail="您不是该群组成员")
    if member.role == GroupRole.OWNER:
        raise HTTPException(status_code=400, detail="群主不能直接退出，请先转让群主或解散群组")
    db.delete(member)
    group.member_count = max(0, group.member_count - 1)
    db.commit()
    return ApiResponse(code=200, message="已退出群组", data={"status": "left"})


def _review_member(group_id: int, target_user_id: int, action: str, reviewer: User, db: Session):
    group = _group_or_404(db, group_id)
    reviewer_member = _membership(db, group_id, reviewer.id)
    if reviewer_member is None or reviewer_member.role not in (GroupRole.OWNER, GroupRole.ADMIN):
        raise HTTPException(status_code=403, detail="需要群组管理权限")
    member = _membership(db, group_id, target_user_id)
    if member is None:
        raise HTTPException(status_code=404, detail="成员不存在")
    if member.status != MemberStatus.PENDING:
        raise HTTPException(status_code=400, detail="该申请已处理")
    member.status = MemberStatus.APPROVED if action == "approve" else MemberStatus.REJECTED
    if member.status == MemberStatus.APPROVED:
        group.member_count += 1
        create_notification(
            db, target_user_id, NotificationType.GROUP_APPROVED,
            title="加群申请已通过",
            content=f"你已成功加入 {group.name}",
            target_type="group", target_id=group.id, sender_id=reviewer.id,
        )
    else:
        create_notification(
            db, target_user_id, NotificationType.GROUP_REJECTED,
            title="加群申请被拒绝",
            content=f"你申请加入 {group.name} 的请求已被拒绝",
            target_type="group", target_id=group.id, sender_id=reviewer.id,
        )
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


@router.delete("/groups/{group_id}/members/{user_id}")
def remove_group_member(
    group_id: int,
    user_id: int,
    reviewer: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    group = _group_or_404(db, group_id)
    reviewer_member = _membership(db, group_id, reviewer.id)
    if reviewer_member is None or reviewer_member.role not in (GroupRole.OWNER, GroupRole.ADMIN):
        raise HTTPException(status_code=403, detail="需要群组管理权限")
    target = _membership(db, group_id, user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="该用户不在群组中")
    if target.role == GroupRole.OWNER:
        raise HTTPException(status_code=400, detail="不能移出群主")
    db.delete(target)
    group.member_count = max(0, group.member_count - 1)
    db.commit()
    return ApiResponse(code=200, message="已移出成员", data={"status": "removed"})


@router.delete("/groups/{group_id}")
def delete_group(
    group_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    group = _group_or_404(db, group_id)
    member = _membership(db, group_id, user.id)
    if member is None or member.role != GroupRole.OWNER:
        raise HTTPException(status_code=403, detail="只有群主可以解散群组")
    db.delete(group)
    db.commit()
    return ApiResponse(code=200, message="群组已解散", data={"status": "deleted"})


@router.put("/groups/{group_id}")
def update_group(
    group_id: int,
    data: GroupUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    group = _group_or_404(db, group_id)
    member = _membership(db, group_id, user.id)
    if member is None or member.role not in (GroupRole.OWNER, GroupRole.ADMIN):
        raise HTTPException(status_code=403, detail="需要群组管理权限")
    if data.name is not None:
        existing = db.query(Group).filter(Group.name == data.name, Group.id != group_id).first()
        if existing:
            raise HTTPException(status_code=409, detail="群组名称已存在")
        group.name = data.name
    if data.description is not None:
        group.description = data.description
    if data.avatar_url is not None:
        group.avatar_url = data.avatar_url
    if data.visibility is not None:
        group.visibility = GroupVisibility(data.visibility)
    if data.need_approval is not None:
        group.need_approval = data.need_approval
    db.commit()
    return ApiResponse(code=200, message="群组信息已更新", data=_group_payload(group, member))


@router.post("/groups/{group_id}/posts", status_code=201)
def create_group_post(
    group_id: int,
    data: GroupPostCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _group_or_404(db, group_id)
    member = _membership(db, group_id, user.id)
    if member is None or member.status != MemberStatus.APPROVED:
        raise HTTPException(status_code=403, detail="只有群组成员可以发帖")
    # 群组帖自动分配到默认板块（第一个活跃板块），若不存在则创建
    category = db.query(Category).filter(Category.is_active.is_(True)).order_by(Category.sort_order).first()
    if category is None:
        category = Category(name="群组讨论", description="群组帖子默认板块", sort_order=999)
        db.add(category)
        db.flush()
    post = Post(
        user_id=user.id,
        category_id=category.id,
        title=data.title,
        content=data.content,
        post_type=PostType.NORMAL,
        status=PostStatus.PUBLISHED,
        tags=data.tags,
    )
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
    payload = {
        "id": message.id,
        "sender_id": message.sender_id,
        "content": message.content,
        "message_type": message.message_type.value,
        "attachment_url": message.attachment_url,
        "is_read": message.is_read,
        "created_at": message.created_at,
    }
    if message.group_id is not None:
        payload["group_id"] = message.group_id
        if message.group:
            payload["group"] = {
                "id": message.group.id,
                "name": message.group.name,
                "avatar_url": message.group.avatar_url,
            }
        if message.sender:
            payload["sender"] = {
                "id": message.sender.id,
                "nickname": message.sender.nickname,
                "avatar_url": message.sender.avatar_url,
            }
    else:
        payload["receiver_id"] = message.receiver_id
        other = message.receiver if message.sender_id == current_user_id else message.sender
        if other:
            payload["other_user"] = {
                "id": other.id,
                "nickname": other.nickname,
                "avatar_url": other.avatar_url,
            }
    return payload


@router.post("/messages", status_code=201)
def send_message(
    data: MessageCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # ── Group message path ──
    if data.group_id:
        group = db.query(Group).filter(Group.id == data.group_id).first()
        if group is None:
            raise HTTPException(status_code=404, detail="群组不存在")
        member = _membership(db, group.id, user.id)
        if member is None or member.status != MemberStatus.APPROVED:
            raise HTTPException(status_code=403, detail="只有群组成员可以发送消息")
        message = Message(
            sender_id=user.id,
            receiver_id=None,
            group_id=group.id,
            content=data.content.strip(),
            message_type=MessageType(data.message_type),
            attachment_url=data.attachment_url,
            is_read=True,
        )
        db.add(message)
        db.flush()
        preview = message.content[:50]
        if len(message.content) > 50:
            preview += "..."
        other_members = db.query(GroupMember).filter(
            GroupMember.group_id == group.id,
            GroupMember.status == MemberStatus.APPROVED,
            GroupMember.user_id != user.id,
        ).all()
        for m in other_members:
            create_notification(
                db, m.user_id, NotificationType.NEW_GROUP_MESSAGE,
                title=f"[群聊] {group.name}",
                content=f"{user.nickname}: {preview}",
                target_type="group_message", target_id=message.id, sender_id=user.id,
            )
        db.commit()
        db.refresh(message)
        return ApiResponse(code=201, message="发送成功", data={"id": message.id})

    # ── DM path ──
    if data.receiver_id == user.id:
        raise HTTPException(status_code=400, detail="不能给自己发私信")
    receiver = db.query(User).filter(User.id == data.receiver_id, User.status == UserStatus.ACTIVE).first()
    if receiver is None:
        raise HTTPException(status_code=404, detail="接收用户不存在")

    # ── Privacy: message_permission ──
    receiver_privacy = receiver.privacy_settings or {}
    msg_permission = receiver_privacy.get("message_permission", "everyone")
    if msg_permission == "none":
        raise HTTPException(status_code=403, detail="该用户已关闭私信功能")
    if msg_permission == "followers_only":
        is_follower = db.query(Follow).filter(
            Follow.follower_id == user.id, Follow.following_id == receiver.id,
        ).first() is not None
        if not is_follower:
            raise HTTPException(status_code=403, detail="仅粉丝可发送私信")

    message = Message(
        sender_id=user.id,
        receiver_id=receiver.id,
        group_id=None,
        content=data.content.strip(),
        message_type=MessageType(data.message_type),
        attachment_url=data.attachment_url,
    )
    db.add(message)
    db.flush()
    create_notification(
        db, receiver.id, NotificationType.NEW_MESSAGE,
        title="收到新私信",
        content=f"{user.nickname}: {message.content[:50]}{'...' if len(message.content) > 50 else ''}",
        target_type="message", target_id=message.id, sender_id=user.id,
    )
    db.commit()
    db.refresh(message)
    return ApiResponse(code=201, message="发送成功", data={"id": message.id})


@router.get("/messages")
def list_messages(
    other_user_id: int | None = None,
    group_id: int | None = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # ── Group messages mode ──
    if group_id is not None:
        group = _group_or_404(db, group_id)
        member = _membership(db, group_id, user.id)
        if member is None or member.status != MemberStatus.APPROVED:
            raise HTTPException(status_code=403, detail="只有群组成员可查看")
        base = db.query(Message).options(
            joinedload(Message.sender), joinedload(Message.group)
        ).filter(Message.group_id == group_id)
        total = base.count()
        messages = base.order_by(Message.created_at.desc()).offset((page - 1) * size).limit(size).all()
        return ApiResponse(code=200, message="success", data={
            "items": [_message_payload(m, user.id) for m in messages],
            "total": total, "page": page, "size": size,
        })

    # ── DM / conversation list mode ──
    base = db.query(Message).options(joinedload(Message.sender), joinedload(Message.receiver), joinedload(Message.group)).filter(
        or_(Message.sender_id == user.id, Message.receiver_id == user.id)
    )
    if other_user_id is not None:
        base = base.filter(or_(
            and_(Message.sender_id == user.id, Message.receiver_id == other_user_id),
            and_(Message.sender_id == other_user_id, Message.receiver_id == user.id),
        ))
    total = base.count()
    messages = base.order_by(Message.created_at.desc()).offset((page - 1) * size).limit(size).all()
    # 仅标记当前页中属于当前用户的未读消息为已读
    if other_user_id is not None:
        unread_ids = [
            m.id for m in messages
            if m.receiver_id == user.id and m.is_read is False
        ]
        if unread_ids:
            db.query(Message).filter(Message.id.in_(unread_ids)).update(
                {Message.is_read: True}, synchronize_session=False
            )
            db.commit()
            # 刷新当前页消息的 is_read 状态
            for m in messages:
                if m.id in unread_ids:
                    m.is_read = True
    if other_user_id is None:
        # 会话列表：DM 按对方去重 + 群聊按 group_id 去重（取每会话最新一条）
        latest_dm: dict[int, Message] = {}
        latest_group: dict[int, Message] = {}
        for message in messages:
            if message.group_id is not None:
                latest_group.setdefault(message.group_id, message)
            else:
                other_id = message.receiver_id if message.sender_id == user.id else message.sender_id
                latest_dm.setdefault(other_id, message)
        dm_items = sorted(latest_dm.values(), key=lambda m: m.created_at, reverse=True)
        group_items = sorted(latest_group.values(), key=lambda m: m.created_at, reverse=True)
        messages = dm_items + group_items
        # 按时间排序合并
        messages.sort(key=lambda m: m.created_at, reverse=True)
    return ApiResponse(code=200, message="success", data={
        "items": [_message_payload(item, user.id) for item in messages],
        "total": total, "page": page, "size": size,
    })


@router.delete("/messages/{message_id}")
def delete_message(
    message_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    message = db.query(Message).filter(Message.id == message_id).first()
    if message is None:
        raise HTTPException(status_code=404, detail="消息不存在")
    if message.sender_id != user.id:
        raise HTTPException(status_code=403, detail="只能删除自己发送的消息")
    db.delete(message)
    db.commit()
    return ApiResponse(code=200, message="消息已删除", data={"status": "deleted"})
