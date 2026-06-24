from __future__ import annotations

import re
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.models.operations import ComplianceCategory, ComplianceRule, SensitiveLevel

_LEVEL_PRIORITY = {
    SensitiveLevel.WARN: 1,
    SensitiveLevel.REVIEW: 2,
    SensitiveLevel.BLOCK: 3,
}


@dataclass
class ComplianceMatch:
    rule_id: int
    rule_name: str
    category: ComplianceCategory
    severity: SensitiveLevel
    matched_text: str
    description: str | None = None


@dataclass
class ComplianceCheckResult:
    level: SensitiveLevel | None = None
    matches: list[ComplianceMatch] = field(default_factory=list)

    @property
    def should_block(self) -> bool:
        return self.level == SensitiveLevel.BLOCK

    @property
    def should_review(self) -> bool:
        return self.level == SensitiveLevel.REVIEW

    @property
    def categories(self) -> list[str]:
        return list({m.category.value for m in self.matches})


def _compile_pattern(pattern: str) -> re.Pattern | None:
    try:
        return re.compile(pattern, re.IGNORECASE)
    except re.error:
        return None


def check_compliance(db: Session, texts: list[str | None]) -> ComplianceCheckResult:
    """对多条文本执行合规检查，返回最高严重级别及所有匹配详情。"""
    active_rules = (
        db.query(ComplianceRule)
        .filter(ComplianceRule.is_active.is_(True))
        .all()
    )
    normalized = [t for t in texts if t and t.strip()]
    if not active_rules or not normalized:
        return ComplianceCheckResult()

    matches: list[ComplianceMatch] = []
    highest_level: SensitiveLevel | None = None

    for rule in active_rules:
        pattern = _compile_pattern(rule.pattern)
        if pattern is None:
            continue
        for text in normalized:
            m = pattern.search(text)
            if m:
                matches.append(ComplianceMatch(
                    rule_id=rule.id,
                    rule_name=rule.name,
                    category=rule.category,
                    severity=rule.severity,
                    matched_text=m.group(),
                    description=rule.description,
                ))
                if highest_level is None or _LEVEL_PRIORITY[rule.severity] > _LEVEL_PRIORITY[highest_level]:
                    highest_level = rule.severity
                break  # 每条规则每条文本只匹配一次

    return ComplianceCheckResult(level=highest_level, matches=matches)


def check_compliance_single_text(db: Session, text: str) -> ComplianceCheckResult:
    """对单个文本执行合规检查的便捷封装。"""
    return check_compliance(db, [text])
