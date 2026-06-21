from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.operations import SensitiveLevel, SensitiveWord


_LEVEL_PRIORITY = {
    SensitiveLevel.WARN: 1,
    SensitiveLevel.REVIEW: 2,
    SensitiveLevel.BLOCK: 3,
}


@dataclass
class SensitiveCheckResult:
    level: SensitiveLevel | None
    matched_words: list[str]

    @property
    def should_block(self) -> bool:
        return self.level == SensitiveLevel.BLOCK

    @property
    def should_review(self) -> bool:
        return self.level == SensitiveLevel.REVIEW


def _contains_word(text: str, word: str) -> bool:
    if not text or not word:
        return False
    lower_text = text.lower()
    lower_word = word.lower()
    return lower_word in lower_text or word in text


def check_sensitive_texts(db: Session, texts: list[str | None]) -> SensitiveCheckResult:
    active_words = (
        db.query(SensitiveWord)
        .filter(SensitiveWord.is_active.is_(True))
        .all()
    )
    normalized_texts = [text for text in texts if text and text.strip()]
    if not active_words or not normalized_texts:
        return SensitiveCheckResult(level=None, matched_words=[])

    matched_words: list[str] = []
    highest_level: SensitiveLevel | None = None

    for item in active_words:
        if any(_contains_word(text, item.word) for text in normalized_texts):
            matched_words.append(item.word)
            if highest_level is None or _LEVEL_PRIORITY[item.level] > _LEVEL_PRIORITY[highest_level]:
                highest_level = item.level

    return SensitiveCheckResult(level=highest_level, matched_words=matched_words)
