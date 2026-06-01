import re
from dataclasses import dataclass
from typing import List, Optional

from core.config import AgentConfig, estimate_tokens


@dataclass
class ValidationResult:
    passed: bool
    confidence: str  # high | medium | low
    issues: List[str]
    sanitized: str


def detect_loops(text: str, history: List[str]) -> Optional[str]:
    if len(history) < 3:
        return None
    recent = history[-3:]
    if len(set(recent)) == 1 and len(recent[0]) > 50:
        return "Content repetition loop detected"
    return None


def check_hallucination(text: str, query: str) -> List[str]:
    issues = []
    if not text or len(text.strip()) < 5:
        issues.append("Empty or near-empty response")
    return issues


def check_consistency(text: str) -> List[str]:
    issues = []
    contradictions = re.findall(r"(?i)(on the one hand|however|but|although|nevertheless)", text)
    if len(contradictions) > 3:
        issues.append("Multiple hedging: overly contradictory phrasing")
    return issues


def validate_response(text: str, query: str, history: List[str]) -> ValidationResult:
    issues = []

    hallucination_issues = check_hallucination(text, query)
    issues.extend(hallucination_issues)

    consistency_issues = check_consistency(text)
    issues.extend(consistency_issues)

    loop_issue = detect_loops(text, [query] + history[-2:] if history else [query])
    if loop_issue:
        issues.append(loop_issue)

    if issues:
        return ValidationResult(False, "low", issues, text)

    token_count = estimate_tokens(text)
    if token_count < 3:
        return ValidationResult(True, "low", ["Very short response"], text)
    if token_count < 20:
        return ValidationResult(True, "medium", ["Short response"], text)

    return ValidationResult(True, "high", [], text)
