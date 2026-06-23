from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.notification import Notification, NotificationType
from app.models.user import User
from app.schemas.user import ApiResponse

router = APIRouter(tags=["notifications"])


def create_notification(
    db: Session,
    user_id: int,
    type: NotificationType,
    title: str,
    content: str,
    target_type: str | None = None,
    target_id: int | None = None,
    sender_id: int | None = None,
) -> Notification:
    notification = Notification(
        user_id=user_id,
        type=type,
        title=title,
        content=content,
        target_type=target_type,
        target_id=target_id,
        sender_id=sender_id,
    )
    db.add(notification)
    return notification


@router.get("/notifications")
def list_notifications(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=50),
    type: str | None = Query(None, pattern="^(follow|group_invite|group_join_request|group_approved|group_rejected|new_message|new_group_message|mention|system)$"),
    unread_only: bool = Query(False),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Notification).options(joinedload(Notification.sender)).filter(
        Notification.user_id == user.id
    )
    if type is not None:
        query = query.filter(Notification.type == type)
    if unread_only:
        query = query.filter(Notification.is_read.is_(False))
    total = query.count()
    items = query.order_by(Notification.created_at.desc()).offset((page - 1) * size).limit(size).all()
    return ApiResponse(code=200, message="success", data={
        "items": [
            {
                "id": n.id,
                "type": n.type.value,
                "title": n.title,
                "content": n.content,
                "is_read": n.is_read,
                "target_type": n.target_type,
                "target_id": n.target_id,
                "sender": {
                    "id": n.sender.id,
                    "nickname": n.sender.nickname,
                    "avatar_url": n.sender.avatar_url,
                } if n.sender else None,
                "created_at": n.created_at,
            }
            for n in items
        ],
        "total": total,
        "page": page,
        "size": size,
    })


@router.put("/notifications/read")
def mark_notifications_read(
    notification_ids: list[int] | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """标记通知为已读。不传 notification_ids 则标记全部未读通知为已读。"""
    query = db.query(Notification).filter(
        Notification.user_id == user.id, Notification.is_read.is_(False)
    )
    if notification_ids:
        query = query.filter(Notification.id.in_(notification_ids))
    count = query.update({Notification.is_read: True}, synchronize_session=False)
    db.commit()
    return ApiResponse(code=200, message=f"已标记 {count} 条通知为已读", data={"marked_count": count})


@router.get("/notifications/unread-count")
def unread_notification_count(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    count = db.query(Notification).filter(
        Notification.user_id == user.id, Notification.is_read.is_(False)
    ).count()
    return ApiResponse(code=200, message="success", data={"unread_count": count})
