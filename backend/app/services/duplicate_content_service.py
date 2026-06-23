from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher

from sqlalchemy.orm import Session

from app.models.content import Post


MIN_DUPLICATE_TEXT_LENGTH = 20
RECENT_POST_LIMIT = 50
NEAR_DUPLICATE_THRESHOLD = 0.92


@dataclass
class DuplicateContentCheckResult:
    status: str = "ok"
    should_block: bool = False
    should_review: bool = False
    matched_post_id: int | None = None
    similarity: float | None = None
    reason: str | None = None


def _normalize_text(*texts: str | None) -> str:
    combined = " ".join(text.strip() for text in texts if text and text.strip())
    if not combined:
        return ""

    normalized = unicodedata.normalize("NFKC", combined).lower()
    normalized = "".join(
        char
        for char in normalized
        if not unicodedata.category(char).startswith(("P", "S"))
    )
    return re.sub(r"\s+", " ", normalized).strip()


def check_duplicate_post_content(
    db: Session,
    user_id: int,
    title: str | None,
    content: str | None,
) -> DuplicateContentCheckResult:
    normalized_text = _normalize_text(title, content)
    if len(normalized_text) < MIN_DUPLICATE_TEXT_LENGTH:
        return DuplicateContentCheckResult(reason="text_too_short")

    recent_posts = (
        db.query(Post)
        .filter(Post.user_id == user_id)
        .order_by(Post.created_at.desc(), Post.id.desc())
        .limit(RECENT_POST_LIMIT)
        .all()
    )

    best_match_id: int | None = None
    best_similarity = 0.0

    for item in recent_posts:
        existing_normalized = _normalize_text(item.title, item.content)
        if len(existing_normalized) < MIN_DUPLICATE_TEXT_LENGTH:
            continue

        if existing_normalized == normalized_text:
            return DuplicateContentCheckResult(
                status="exact_duplicate",
                should_block=True,
                matched_post_id=item.id,
                similarity=1.0,
                reason="exact_duplicate_post",
            )

        similarity = SequenceMatcher(None, normalized_text, existing_normalized).ratio()
        if similarity > best_similarity:
            best_similarity = similarity
            best_match_id = item.id

    if best_match_id is not None and best_similarity >= NEAR_DUPLICATE_THRESHOLD:
        return DuplicateContentCheckResult(
            status="near_duplicate",
            should_review=True,
            matched_post_id=best_match_id,
            similarity=best_similarity,
            reason="near_duplicate_post",
        )

    return DuplicateContentCheckResult(reason="no_duplicate_detected")
