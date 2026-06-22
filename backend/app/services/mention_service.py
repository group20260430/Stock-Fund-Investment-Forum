"""@mention parsing and notification dispatch."""

import re

from sqlalchemy.orm import Session

from app.models.notification import Notification, NotificationType
from app.models.user import User
from app.api.notifications import create_notification


def parse_mentions(content: str) -> list[str]:
    """
    Extract @username patterns from content.

    Pattern rules:
    - Must start with @ preceded by whitespace or start of string
    - Valid characters: Chinese chars, letters, digits, underscores, hyphens
    - Must be followed by whitespace, punctuation, or end of string
    - Max username length: 50 (matching User.nickname column)
    - Returns deduplicated list of usernames
    """
    if not content:
        return []

    # (?:^|[\s]) ensures @ is at start or after whitespace (prevents email@domain match)
    # [一-鿿\w\-]{1,50} matches Chinese chars, word chars, hyphens
    # (?=[\s,.;:!?，。；：！？]|$) ensures followed by whitespace/punctuation/end
    # NOTE: Use non-capturing prefix instead of lookbehind because Python re
    #       does not support variable-width alternatives in lookbehind.
    pattern = r'(?:^|[\s])@([一-鿿\w\-]{1,50})(?=[\s,.;:!?，。；：！？]|$)'
    matches = re.findall(pattern, content)
    return list(set(matches))  # deduplicate


def validate_mentions(db: Session, usernames: list[str]) -> dict[str, int]:
    """
    Resolve usernames to user IDs.

    Returns a dict of {username: user_id} for existing users only.
    Non-existent usernames are silently ignored.
    """
    if not usernames:
        return {}
    users = db.query(User).filter(User.nickname.in_(usernames)).all()
    return {u.nickname: u.id for u in users}


def create_mention_notifications(
    db: Session,
    mentioned_user_ids: list[int],
    sender_id: int,
    source_type: str,
    source_id: int,
) -> None:
    """
    Create MENTION notifications for each mentioned user.

    Skips self-mentions and duplicate notifications for the same (user, source_type, source_id).
    """
    for uid in mentioned_user_ids:
        if uid == sender_id:
            continue

        # Check for existing notification to avoid duplicates on post edits
        existing = db.query(Notification.id).filter(
            Notification.user_id == uid,
            Notification.type == NotificationType.MENTION,
            Notification.target_type == source_type,
            Notification.target_id == source_id,
        ).first()
        if existing:
            continue

        create_notification(
            db,
            uid,
            NotificationType.MENTION,
            title="有人提到了你",
            content=f"有用户在{source_type}中提到了你",
            target_type=source_type,
            target_id=source_id,
            sender_id=sender_id,
        )
