import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from sqlalchemy.orm import Session

from core.database import AuditLog
from core.config import AgentConfig, estimate_tokens
from core.prompts import TOOL_REGISTRY


class AuditLogger:
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.prompt_log_enabled = os.getenv("PROMPT_LOG_ENABLED", "true").lower() not in {"0", "false", "no"}
        self.prompt_log_dir = Path(os.getenv("PROMPT_LOG_DIR", "logs/system_prompts"))

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

    def log_system_prompt(
        self,
        *,
        user_id: int,
        username: str,
        conversation_id: str,
        model: str,
        messages: list[dict[str, str]],
        tools: Optional[dict[str, Any]] = None,
        tool_events: Optional[list[dict[str, Any]]] = None,
        options: Optional[dict[str, Any]] = None,
        ip: str = "",
    ) -> Optional[str]:
        if not self.enabled or not self.prompt_log_enabled:
            return None

        try:
            now = datetime.now(timezone.utc)
            day_dir = self.prompt_log_dir / now.strftime("%Y-%m-%d")
            day_dir.mkdir(parents=True, exist_ok=True)

            safe_conversation_id = "".join(
                ch if ch.isalnum() or ch in {"-", "_"} else "_"
                for ch in conversation_id
            )[:80]
            filename = f"{now.strftime('%H%M%S_%f')}_user-{user_id}_{safe_conversation_id}.json"
            path = day_dir / filename

            system_messages = [m.get("content", "") for m in messages if m.get("role") == "system"]
            tool_registry = tools or TOOL_REGISTRY
            events = tool_events or []
            payload = {
                "timestamp": now.isoformat(),
                "event": "system_prompt_built",
                "user_id": user_id,
                "username": username,
                "conversation_id": conversation_id,
                "model": model,
                "ip_address": ip,
                "options": options or {},
                "tools": tool_registry,
                "tool_events": events,
                "react_messages": self._build_react_messages(messages, events),
                "system_prompt": "\n\n".join(system_messages),
                "messages": messages,
                "message_count": len(messages),
                "estimated_total_tokens": estimate_tokens("\n".join(m.get("content", "") for m in messages)),
            }

            path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            return str(path)
        except Exception:
            return None

    def _build_react_messages(self, messages: list[dict[str, str]], tool_events: list[dict[str, Any]]) -> list[dict[str, Any]]:
        react_messages: list[dict[str, Any]] = list(messages)
        for event in tool_events:
            name = event.get("name", "unknown_tool")
            args = event.get("args", {})
            status = event.get("status", "ok")
            result = event.get("result", {})
            react_messages.append({
                "role": "assistant",
                "content": f"Action: {name}({json.dumps(args, ensure_ascii=False)})",
            })
            react_messages.append({
                "role": "tool",
                "name": name,
                "content": json.dumps({
                    "status": status,
                    "result": result,
                }, ensure_ascii=False),
            })
        return react_messages


logger = AuditLogger()
