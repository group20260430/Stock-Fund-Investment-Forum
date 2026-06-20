from sqlalchemy.orm import Session

from app.models.operations import ActivityType, UserActivityLog


def record_activity(
    db: Session,
    user_id: int,
    activity_type: ActivityType,
    target_type: str | None = None,
    target_id: int | None = None,
) -> None:
    db.add(
        UserActivityLog(
            user_id=user_id,
            activity_type=activity_type,
            target_type=target_type,
            target_id=target_id,
        )
    )
