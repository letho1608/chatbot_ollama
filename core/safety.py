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
            found.append(f"{pii_type}:{m}")
            result = result.replace(m, f"[{pii_type.upper()}]")
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
    sanitized, pii_list = sanitize_pii(text)
    if pii_list:
        return SafetyResult(True, f"PII removed: {len(pii_list)} item(s)", sanitized, pii_list)
    return SafetyResult(True, "", text)


def validate_output(text: str) -> SafetyResult:
    return check_content_safety(text)
