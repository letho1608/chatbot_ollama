import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from core.config import AgentConfig, estimate_tokens
from core.memory import extract_memories_from_text, format_memories_for_prompt, resolve_memory_conflict
from core.monitor import logger
from core.prompts import build_system_prompt
from core.safety import validate_input, validate_output
from core.validator import validate_response, ValidationResult


@dataclass
class AgentContext:
    user_id: int
    username: str
    query: str
    conversation_id: str
    model: str
    system_prompt: str = ""
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 40
    max_tokens: int = 2048
    history_messages: list = field(default_factory=list)
    start_time: float = 0.0
    safety_result: Any = None
    validation_result: Any = None


class AgentOrchestrator:
    def __init__(self, config: Optional[AgentConfig] = None):
        self.config = config or AgentConfig()

    def process_input(self, ctx: AgentContext, db: Session, ip: str = "") -> Tuple[bool, Optional[str]]:
        if self.config.safety_enabled:
            result = validate_input(ctx.query)
            if not result.passed:
                logger.log(ctx.user_id, "safety_block", {
                    "reason": result.reason, "query": ctx.query[:100]
                }, ip, db)
                return False, result.reason
            ctx.safety_result = result
            if result.sanitized:
                ctx.query = result.sanitized
        return True, None

    def build_ollama_messages(self, ctx: AgentContext, db: Session) -> List[Dict[str, str]]:
        system_parts = []
        if ctx.system_prompt:
            system_parts.append(ctx.system_prompt)

        if self.config.memory_enabled:
            memories = format_memories_for_prompt(ctx.user_id, db)
            if memories:
                system_parts.append(memories)

        try:
            from core.rag import hybrid_retrieve, format_rag_context
            rag_results = hybrid_retrieve(ctx.user_id, ctx.query)
            rag_ctx = format_rag_context(rag_results)
            if rag_ctx:
                system_parts.append(rag_ctx)
        except Exception:
            pass

        messages = [{"role": "system", "content": build_system_prompt(system_parts)}]

        history = self._trim_history(ctx.history_messages, ctx.query)
        if len(history) < len(ctx.history_messages):
            messages.append({
                "role": "system",
                "content": "Một phần lịch sử hội thoại cũ đã được rút gọn để giữ context window ổn định.",
            })

        for m in history:
            messages.append({"role": m.role, "content": m.content})

        messages.append({"role": "user", "content": ctx.query})
        return messages

    def _trim_history(self, history_messages: list, query: str) -> list:
        if not history_messages:
            return []

        recent = list(history_messages)[-self.config.max_history_messages:]
        budget = max(self.config.max_context_tokens - estimate_tokens(query), 512)
        selected = []
        used = 0

        for msg in reversed(recent):
            cost = estimate_tokens(getattr(msg, "content", ""))
            if selected and used + cost > budget:
                break
            selected.append(msg)
            used += cost

        return list(reversed(selected))

    def process_response(
        self,
        ctx: AgentContext,
        response_text: str,
        db: Session,
        ip: str = "",
        max_tokens: Optional[int] = None,
        truncated: bool = False,
    ):
        elapsed_ms = int((time.time() - ctx.start_time) * 1000)

        if self.config.output_validation_enabled:
            history = [m.content for m in ctx.history_messages if m.role == "assistant"]
            ctx.validation_result = validate_response(response_text, ctx.query, history)
            if ctx.validation_result.confidence == "low" and ctx.validation_result.issues:
                logger.log(ctx.user_id, "low_confidence_response", {
                    "issues": ctx.validation_result.issues,
                    "response_preview": response_text[:100],
                }, ip, db)

        if self.config.safety_enabled:
            safety = validate_output(response_text)
            if not safety.passed:
                logger.log(ctx.user_id, "output_safety_block", {
                    "reason": safety.reason,
                    "response_preview": response_text[:100],
                }, ip, db)

        if self.config.memory_enabled:
            extract_memories_from_text(ctx.user_id, ctx.query, db)

        if self.config.audit_enabled:
            logger.log_chat(
                ctx.user_id, ctx.query, response_text, ctx.model, elapsed_ms, db, ip,
                safety_flagged=bool(ctx.safety_result and ctx.safety_result.pii_found),
                max_tokens=max_tokens,
                truncated=truncated,
                username=ctx.username,
                conversation_id=ctx.conversation_id,
            )

    def should_plan(self, query: str) -> bool:
        if not self.config.planning_enabled:
            return False
        word_count = len(query.split())
        return word_count > self.config.complex_query_min_words

    def get_adaptive_config(self, query: str) -> Dict[str, Any]:
        if not self.config.adaptive_scale:
            return {}
        word_count = len(query.split())
        if word_count <= self.config.short_query_max_words:
            return {"max_tokens": 512, "temperature": 0.7}
        elif word_count >= self.config.complex_query_min_words:
            return {"max_tokens": 4096, "temperature": 0.8}
        return {"max_tokens": 2048, "temperature": 0.7}
