"""Points and level system — award points and calculate user levels."""

from sqlalchemy.orm import Session

from app.models.points import PointsHistory
from app.models.user import User


# Level thresholds: list of (min_points, level) in ascending order
LEVEL_THRESHOLDS = [
    (100, 2),
    (300, 3),
    (600, 4),
    (1000, 5),
    (2000, 6),
    (5000, 7),
    (10000, 8),
]


def get_level(points: int) -> int:
    """Calculate level from total points using the threshold table."""
    level = 1
    for threshold, lvl in LEVEL_THRESHOLDS:
        if points >= threshold:
            level = lvl
        else:
            break
    return level


def award_points(
    db: Session,
    user_id: int,
    points: int,
    reason: str,
    reference_type: str | None = None,
    reference_id: int | None = None,
) -> None:
    """
    Award points to a user and update their level.

    - `points` can be negative for deductions (not currently used)
    - Does NOT commit — the caller should commit
    """
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        return

    user.points = (user.points or 0) + points
    user.level = get_level(user.points)

    db.add(
        PointsHistory(
            user_id=user_id,
            points_change=points,
            reason=reason,
            reference_type=reference_type,
            reference_id=reference_id,
        )
    )
