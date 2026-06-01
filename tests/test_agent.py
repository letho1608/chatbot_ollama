"""Agent framework tests: orchestrator, context, config, adaptive params."""

from types import SimpleNamespace

from core.agent import AgentOrchestrator, AgentContext, AgentConfig

from core.config import MODEL_CATALOG, MODEL_CATEGORIES, SECURITY_KEYWORDS
from core.monitor import AuditLogger
from core.prompts import build_system_prompt


class TestAgentContext:
    def test_create_context(self):
        ctx = AgentContext(
            user_id=1, username="test", query="What is a firewall?",
            conversation_id="conv-1", model="minimax-m3:cloud"
        )
        assert ctx.user_id == 1
        assert ctx.username == "test"
        assert ctx.query == "What is a firewall?"

    def test_context_defaults(self):
        ctx = AgentContext(1, "test", "hello", "conv-default", "minimax-m3:cloud")
        assert ctx.temperature == 0.7
        assert ctx.max_tokens == 2048
        assert ctx.top_p == 0.9
        assert ctx.top_k == 40


class TestAgentOrchestrator:
    def test_init(self):
        agent = AgentOrchestrator()
        assert agent is not None

    def test_get_adaptive_config_short(self):
        agent = AgentOrchestrator()
        cfg = agent.get_adaptive_config("Hello")
        assert cfg["max_tokens"] == 512
        assert cfg["temperature"] == 0.7

    def test_get_adaptive_config_medium(self):
        agent = AgentOrchestrator()
        cfg = agent.get_adaptive_config("What is the best way to secure a network from external threats and internal vulnerabilities")
        assert cfg["max_tokens"] == 2048

    def test_get_adaptive_config_long(self):
        agent = AgentOrchestrator()
        query = "word " * 60
        cfg = agent.get_adaptive_config(query)
        assert cfg["max_tokens"] == 4096
        assert cfg["temperature"] == 0.8

    def test_build_messages_minimal(self, db, normal_user):
        agent = AgentOrchestrator()
        ctx = AgentContext(
            user_id=normal_user.id, username="testuser",
            query="What is SQL injection?",
            conversation_id="test-build-1", model="minimax-m3:cloud",
            system_prompt="You are a security expert."
        )
        msgs = agent.build_ollama_messages(ctx, db)
        assert len(msgs) >= 2
        roles = [m["role"] for m in msgs]
        assert "system" in roles
        assert "user" in roles

    def test_system_prompt_includes_tool_registry_and_error_rules(self):
        prompt = build_system_prompt(["Custom classroom rule."])
        assert "Tool registry" in prompt
        assert "rag_search" in prompt
        assert "Quy tắc xử lý lỗi" in prompt
        assert "Custom classroom rule." in prompt

    def test_build_messages_trims_long_history(self, db, normal_user):
        agent = AgentOrchestrator(AgentConfig(max_history_messages=3, max_context_tokens=80))
        ctx = AgentContext(
            user_id=normal_user.id, username="testuser",
            query="What is firewall hardening?",
            conversation_id="test-build-trim", model="minimax-m3:cloud",
        )
        ctx.history_messages = [
            SimpleNamespace(role="user", content="old " * 200),
            SimpleNamespace(role="assistant", content="middle answer"),
            SimpleNamespace(role="user", content="recent question"),
            SimpleNamespace(role="assistant", content="recent answer"),
        ]
        msgs = agent.build_ollama_messages(ctx, db)
        contents = [m["content"] for m in msgs]
        assert not any("old old old" in c for c in contents)
        assert any("rút gọn" in c for c in contents)

    def test_log_system_prompt_json_file(self, tmp_path):
        logger = AuditLogger()
        logger.prompt_log_dir = tmp_path / "system_prompts"
        path = logger.log_system_prompt(
            user_id=1,
            username="testuser",
            conversation_id="conv-1",
            model="qwen2:7b",
            messages=[
                {"role": "system", "content": "System rules"},
                {"role": "user", "content": "What is a firewall?"},
            ],
            options={"temperature": 0.7},
            ip="127.0.0.1",
        )
        assert path is not None
        assert path.endswith(".json")
        assert "System rules" in open(path, encoding="utf-8").read()


class TestAgentConfig:
    def test_default_config(self):
        cfg = AgentConfig()
        assert cfg.max_history_messages > 0
        assert cfg.max_context_tokens > 0
        assert cfg.safety_enabled is True
        assert cfg.audit_enabled is True
        assert cfg.output_validation_enabled is True

    def test_adaptive_scale(self):
        cfg = AgentConfig()
        assert cfg.adaptive_scale is True
        assert cfg.short_query_max_words == 10
        assert cfg.complex_query_min_words == 50


class TestSecurityKeywords:
    def test_keywords_exist(self):
        assert len(SECURITY_KEYWORDS) > 100

    def test_common_keywords_present(self):
        keywords_lower = [k.lower() for k in SECURITY_KEYWORDS]
        for kw in ["firewall", "encryption", "malware", "phishing"]:
            assert kw in keywords_lower
