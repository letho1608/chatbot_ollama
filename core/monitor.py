import json
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from core.database import AuditLog
from core.config import AgentConfig, estimate_tokens


class AuditLogger:
    def __init__(self, enabled: bool = True):
        self.enabled = enabled

    def log(self, user_id: Optional[int], event: str, detail: Any = None, ip: str = "", db: Optional[Session] = None):
        if not self.enabled:
            return
        entry = AuditLog(
            user_id=user_id,
            event=event,
            detail=detail if isinstance(detail, (dict, list)) else {"msg": str(detail)} if detail else None,
            ip_address=ip,
        )
        if db:
            db.add(entry)
            db.flush()

    def log_chat(self, user_id: int, query: str, response: str, model: str, latency_ms: int, db: Session, ip: str = "", safety_flagged: bool = False):
        detail = {
            "model": model,
            "latency_ms": latency_ms,
            "input_tokens": estimate_tokens(query),
            "output_tokens": estimate_tokens(response),
            "safety_flagged": safety_flagged,
        }
        self.log(user_id, "chat", detail, ip, db)

    def log_login(self, user_id: int, success: bool, db: Session, ip: str = ""):
        self.log(user_id, "login" if success else "login_failed", {"success": success}, ip, db)

    def log_admin(self, admin_id: int, action: str, target_id: int, db: Session, ip: str = ""):
        self.log(admin_id, f"admin_{action}", {"target_user_id": target_id}, ip, db)


logger = AuditLogger()
