"""Content quality scoring service.

Computes a 0–100 quality score for posts and comments based on
objective characteristics: length, structure, formatting, and substance.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


# ── constants ──────────────────────────────────────────────────────────────

_MIN_WORDS = 5          # below this, score is heavily penalised
_GOOD_LENGTH = 100      # chars considered "substantial"
_EXCELLENT_LENGTH = 500 # chars considered "comprehensive"


@dataclass
class QualityScore:
    score: int             # 0–100
    level: str             # "low" | "medium" | "good"
    flags: list[str]       # human-readable notes
    word_count: int
    char_count: int
    has_paragraphs: bool
    has_links: bool


def score_content(text: str | None) -> QualityScore:
    """Compute a basic quality score for a piece of text content.

    The score is derived from:
    1. **Length**          — content that is too short or excessively long is
                              penalised; mid-length content scores highest.
    2. **Structure**       — presence of paragraph breaks boosts score.
    3. **Substance**       — links / references improve score modestly.
    4. **Word diversity**  — ratio of unique words to total words.

    Returns a ``QualityScore`` with a 0–100 score and a level label.
    """
    if not text or not text.strip():
        return QualityScore(score=0, level="low", flags=["empty"],
                            word_count=0, char_count=0,
                            has_paragraphs=False, has_links=False)

    cleaned = text.strip()
    char_count = len(cleaned)

    # word / token extraction (Chinese-aware: split on whitespace + CJK boundaries)
    tokens = _tokenize(cleaned)
    word_count = max(1, len(tokens))

    # ── 1. Length score (0–40) ─────────────────────────────────────────
    if word_count < _MIN_WORDS:
        length_score = 0
    elif char_count < 50:
        length_score = 5
    elif char_count < _GOOD_LENGTH:
        length_score = 20
    elif char_count < _EXCELLENT_LENGTH:
        length_score = 32
    else:
        length_score = 40

    # ── 2. Structure score (0–25) ──────────────────────────────────────
    structure_score = 0
    has_paragraphs = "\n\n" in cleaned or "\r\n\r\n" in cleaned
    if has_paragraphs:
        structure_score += 15
    # check for bullet / numbered list patterns
    if bool(re.search(r"(^|\n)\s*[\d一二三四五六七八九十]+[\.、)]", cleaned)):
        structure_score += 10

    # ── 3. Substance score (0–20) ──────────────────────────────────────
    substance_score = 0
    has_links = bool(re.search(r"https?://", cleaned))
    if has_links:
        substance_score += 10
    # contains data / numbers (stock code, percentages, prices)
    if bool(re.search(r"\d{4,}", cleaned)):
        substance_score += 5
    if bool(re.search(r"\d+\.?\d*%", cleaned)):
        substance_score += 5

    # ── 4. Word diversity (0–15) ───────────────────────────────────────
    diversity_score = 0
    if word_count >= 20:
        unique = len(set(t.lower() for t in tokens))
        ratio = min(1.0, unique / word_count)
        diversity_score = int(ratio * 15)

    total = min(100, length_score + structure_score + substance_score + diversity_score)

    # ── level ──────────────────────────────────────────────────────────
    if total >= 60:
        level = "good"
    elif total >= 30:
        level = "medium"
    else:
        level = "low"

    # ── flags ──────────────────────────────────────────────────────────
    flags = []
    if word_count < _MIN_WORDS:
        flags.append("too_short")
    if char_count > 5000:
        flags.append("very_long")
    if has_links:
        flags.append("has_links")
    if has_paragraphs:
        flags.append("structured")

    return QualityScore(
        score=total,
        level=level,
        flags=flags,
        word_count=word_count,
        char_count=char_count,
        has_paragraphs=has_paragraphs,
        has_links=has_links,
    )


# ── helpers ────────────────────────────────────────────────────────────────

_CJK_RE = re.compile(r"[一-鿿㐀-䶿]+")
_NON_ALPHA_RE = re.compile(r"[^a-zA-Z0-9一-鿿㐀-䶿]+")


def _tokenize(text: str) -> list[str]:
    """Split text into tokens, CJK-aware.

    Latin words are split on whitespace/punctuation; CJK runs are kept as
    whole segments (each CJK character is effectively a "word" in Chinese).
    """
    # Replace non-alphanumeric / non-CJK chars with space, then split
    cleaned = _NON_ALPHA_RE.sub(" ", text)
    parts = cleaned.split()
    tokens: list[str] = []
    for part in parts:
        if _CJK_RE.fullmatch(part):
            # treat each CJK character as a token
            tokens.extend(list(part))
        else:
            tokens.append(part)
    return tokens
