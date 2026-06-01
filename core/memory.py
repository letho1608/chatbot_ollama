import re
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from core.database import Memory


def get_relevant_memories(user_id: int, query: str, db: Session, limit: int = 5) -> List[Memory]:
    memories = db.query(Memory).filter(Memory.user_id == user_id).order_by(Memory.updated_at.desc()).limit(limit).all()
    return memories


def get_memory(user_id: int, key: str, db: Session) -> Optional[Memory]:
    return db.query(Memory).filter(Memory.user_id == user_id, Memory.key == key).first()


def set_memory(user_id: int, key: str, value: str, db: Session, source: str = "conversation", confidence: int = 100) -> Memory:
    existing = get_memory(user_id, key, db)
    if existing:
        existing.value = value
        existing.source = source
        existing.confidence = confidence
        existing.updated_at = datetime.now(timezone.utc)
        db.flush()
        return existing
    mem = Memory(user_id=user_id, key=key, value=value, source=source, confidence=confidence)
    db.add(mem)
    db.flush()
    return mem


def delete_memory(user_id: int, key: str, db: Session) -> bool:
    mem = get_memory(user_id, key, db)
    if mem:
        db.delete(mem)
        db.flush()
        return True
    return False


def resolve_memory_conflict(user_id: int, key: str, new_value: str, db: Session, new_source: str = "conversation") -> bool:
    existing = get_memory(user_id, key, db)
    if not existing:
        set_memory(user_id, key, new_value, db, new_source, 100)
        return True
    if existing.value == new_value:
        existing.confidence = min(100, existing.confidence + 5)
        return True
    if new_source == "manual":
        existing.value = new_value
        existing.confidence = 100
        existing.source = new_source
        return True
    if existing.source == "manual":
        return False
    existing.value = new_value
    existing.confidence = min(100, existing.confidence + 10)
    existing.source = new_source
    return True


def extract_memories_from_text(user_id: int, text: str, db: Session):
    patterns = [
        (r"(?:I am|I'm|my name is)\s+(\w+)", "user_name"),
        (r"I (?:like|love|enjoy)\s+(\w+(?:\s+\w+)?)", "preference"),
        (r"I (?:work|am working)\s+(?:as|at)\s+(\w+(?:\s+\w+)?)", "occupation"),
        (r"I (?:live|stay|reside)\s+(?:in|at)\s+(\w+(?:\s+\w+)?)", "location"),
        (r"I (?:speak|know|understand)\s+(\w+(?:\s+\w+)?)\s*(?:language)?", "language"),
    ]
    for pattern, key in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            set_memory(user_id, key, m.group(1).strip(), db, "conversation", 80)


def format_memories_for_prompt(user_id: int, db: Session) -> str:
    memories = get_relevant_memories(user_id, "", db, 10)
    if not memories:
        return ""
    lines = []
    for m in memories:
        label = m.key.replace("_", " ").title()
        lines.append(f"- {label}: {m.value}")
    return "Known about user:\n" + "\n".join(lines)
