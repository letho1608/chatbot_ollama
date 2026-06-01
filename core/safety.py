import re
from dataclasses import dataclass
from typing import List, Optional, Tuple

from core.config import BLOCKED_PATTERNS, INJECTION_PATTERNS, PII_PATTERNS, SECURITY_KEYWORDS


@dataclass
class SafetyResult:
    passed: bool
    reason: str = ""
    sanitized: str = ""
    pii_found: list = None


def check_content_safety(text: str) -> SafetyResult:
    for category, pattern in BLOCKED_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return SafetyResult(False, f"Blocked: {category}", text)
    return SafetyResult(True, "", text)


def detect_prompt_injection(text: str) -> SafetyResult:
    for pattern in INJECTION_PATTERNS:
        m = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if m:
            return SafetyResult(False, f"Prompt injection detected: {m.group(0)[:60]}", text)
    return SafetyResult(True, "", text)


def sanitize_pii(text: str) -> Tuple[str, List[str]]:
    result = text
    found = []
    for pii_type, pattern in PII_PATTERNS:
        matches = re.findall(pattern, result)
        for m in matches:
            found.append(pii_type)
            result = result.replace(m, f"[{pii_type.upper()}]")
    return result, found


SECRET_PATTERNS: List[Tuple[str, str]] = [
    ("openai_api_key", r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    ("github_token", r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{20,}\b"),
    ("github_fine_grained_token", r"\bgithub_pat_[A-Za-z0-9_]{40,}\b"),
    ("aws_access_key", r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    ("google_api_key", r"\bAIza[0-9A-Za-z_-]{35}\b"),
    ("slack_token", r"\bxox[baprs]-[0-9A-Za-z-]{10,}\b"),
    ("private_key", r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----"),
    ("jwt", r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"),
    ("assignment_secret", r"(?i)\b(api[_-]?key|secret|token|password|passwd|pwd|credential)\b\s*[:=]\s*['\"]?([^\s'\";,]{8,})"),
]


def sanitize_secrets(text: str) -> Tuple[str, List[str]]:
    result = text
    found = []
    for secret_type, pattern in SECRET_PATTERNS:
        matches = list(re.finditer(pattern, result, re.IGNORECASE | re.MULTILINE))
        for match in reversed(matches):
            found.append(secret_type)
            if secret_type == "assignment_secret" and match.lastindex and match.lastindex >= 2:
                value_start, value_end = match.span(2)
                result = result[:value_start] + f"[REDACTED_{secret_type.upper()}]" + result[value_end:]
            else:
                start, end = match.span()
                result = result[:start] + f"[REDACTED_{secret_type.upper()}]" + result[end:]
    return result, found


def sanitize_sensitive(text: str, include_pii: bool = True) -> Tuple[str, List[str]]:
    result, secret_list = sanitize_secrets(text)
    found = [f"secret:{item}" for item in secret_list]
    if include_pii:
        result, pii_list = sanitize_pii(result)
        found.extend(f"pii:{item}" for item in pii_list)
    return result, found


def check_security_relevance(text: str) -> SafetyResult:
    if len(text.strip()) < 3:
        return SafetyResult(False, "Nội dung quá ngắn")
    text_lower = text.lower()
    matches = sum(1 for kw in SECURITY_KEYWORDS if kw in text_lower)
    if matches == 0:
        return SafetyResult(False, "Tysor chỉ hỗ trợ các câu hỏi về Cyber Security. Vui lòng đặt câu hỏi liên quan đến bảo mật, an ninh mạng, mã hóa, hoặc các chủ đề an toàn thông tin khác.")
    return SafetyResult(True, "", text)


GREETING_PATTERNS = [
    r"^(chào|xin chào|hello|hi|hey|hallo|bonjour|hola|hei|hej)$",
    r"^(cảm ơn|cám ơn|thank|thanks|ty|ok|okay|bye|goodbye|tạm biệt)$",
    r"^(có thể|bạn có thể|please|help|giúp|hỗ trợ)",
    r"^(tôi|mình|em|tớ)",
    r"\b(bạn là ai|ai là bạn|what are you|who are you)\b",
]


def is_greeting_or_social(text: str) -> bool:
    text_lower = text.strip().lower()
    for pat in GREETING_PATTERNS:
        if re.search(pat, text_lower):
            return True
    return False


def validate_input(text: str, check_topic: bool = True) -> SafetyResult:
    content = check_content_safety(text)
    if not content.passed:
        return content
    injection = detect_prompt_injection(text)
    if not injection.passed:
        return injection
    if not is_greeting_or_social(text) and check_topic:
        topic = check_security_relevance(text)
        if not topic.passed:
            return topic
    sanitized, sensitive_list = sanitize_sensitive(text)
    if sensitive_list:
        return SafetyResult(True, f"Sensitive data removed: {len(sensitive_list)} item(s)", sanitized, sensitive_list)
    return SafetyResult(True, "", text)


def validate_output(text: str) -> SafetyResult:
    content = check_content_safety(text)
    if not content.passed:
        return content
    sanitized, sensitive_list = sanitize_sensitive(text)
    if sensitive_list:
        return SafetyResult(True, f"Sensitive data removed: {len(sensitive_list)} item(s)", sanitized, sensitive_list)
    return SafetyResult(True, "", text)
