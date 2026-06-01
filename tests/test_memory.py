"""Memory module tests: CRUD, extraction, formatting."""

from core.memory import (
    set_memory, get_memory,
    delete_memory, get_relevant_memories,
    format_memories_for_prompt
)


class TestMemoryCRUD:
    def test_set_and_get(self, db, normal_user):
        set_memory(normal_user.id, "role", "security researcher", db)
        mem = get_memory(normal_user.id, "role", db)
        assert mem is not None
        assert mem.value == "security researcher"

    def test_get_nonexistent(self, db, normal_user):
        mem = get_memory(normal_user.id, "nonexistent_key", db)
        assert mem is None

    def test_update_memory(self, db, normal_user):
        set_memory(normal_user.id, "company", "CyberCorp", db)
        set_memory(normal_user.id, "company", "SecureTech", db)
        mem = get_memory(normal_user.id, "company", db)
        assert mem.value == "SecureTech"

    def test_delete_memory(self, db, normal_user):
        set_memory(normal_user.id, "temp_key", "temp_value", db)
        delete_memory(normal_user.id, "temp_key", db)
        mem = get_memory(normal_user.id, "temp_key", db)
        assert mem is None

    def test_delete_nonexistent(self, db, normal_user):
        delete_memory(normal_user.id, "no_such_key", db)

    def test_get_relevant(self, db, normal_user):
        set_memory(normal_user.id, "k1", "v1", db)
        set_memory(normal_user.id, "k2", "v2", db)
        memories = get_relevant_memories(normal_user.id, "v1", db)
        assert len(memories) >= 1

    def test_empty_user(self, db):
        memories = get_relevant_memories(999, "test", db)
        assert memories == []


class TestMemoryRelevance:
    def test_get_relevant_memories(self, db, normal_user):
        set_memory(normal_user.id, "skill", "penetration testing", db, source="conversation", confidence=90)
        set_memory(normal_user.id, "tool", "Metasploit", db, source="conversation", confidence=80)
        relevant = get_relevant_memories(normal_user.id, "testing tools", db)
        assert len(relevant) >= 1

    def test_format_memories(self, db, normal_user):
        set_memory(normal_user.id, "role", "admin", db)
        set_memory(normal_user.id, "company", "Corp", db)
        formatted = format_memories_for_prompt(normal_user.id, db)
        assert "Role" in formatted
        assert "admin" in formatted
        assert "Company" in formatted
