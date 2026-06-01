"""Config module tests: model catalog, categories, patterns, keywords."""

from core.config import (
    MODEL_CATALOG, MODEL_CATEGORIES,
    SECURITY_KEYWORDS, BLOCKED_PATTERNS, INJECTION_PATTERNS,
    AgentConfig, ModelInfo
)


class TestModelCatalog:
    def test_catalog_not_empty(self):
        assert len(MODEL_CATALOG) > 0

    def test_model_has_required_fields(self):
        for m in MODEL_CATALOG:
            assert m.name
            assert m.category
            assert m.description

    def test_default_model_exists(self):
        names = [m.name for m in MODEL_CATALOG]
        assert "minimax-m3:cloud" in names

    def test_all_categories_present(self):
        cats = set(m.category for m in MODEL_CATALOG)
        for cat in MODEL_CATEGORIES:
            assert cat in cats


class TestCategories:
    def test_categories_not_empty(self):
        assert len(MODEL_CATEGORIES) > 0

    def test_general_category_exists(self):
        assert "general" in [c.lower() for c in MODEL_CATEGORIES]


class TestSecurityKeywords:
    def test_keywords_count(self):
        assert len(SECURITY_KEYWORDS) >= 200

    def test_keywords_are_strings(self):
        for kw in SECURITY_KEYWORDS:
            assert isinstance(kw, str)
            assert len(kw) > 0


class TestBlockedPatterns:
    def test_all_categories_present(self):
        cats = [b[0] for b in BLOCKED_PATTERNS]
        for cat in ["violence", "self_harm", "harassment", "hate_speech",
                     "explicit_adult", "drugs", "weapons", "illegal_access", "phishing"]:
            assert cat in cats

    def test_each_category_has_patterns(self):
        for b in BLOCKED_PATTERNS:
            assert len(b[1]) > 0


class TestInjectionPatterns:
    def test_patterns_exist(self):
        assert len(INJECTION_PATTERNS) >= 20

    def test_dan_pattern_present(self):
        patterns_lower = [p.lower() for p in INJECTION_PATTERNS]
        assert any("dan" in p for p in patterns_lower)


class TestModelInfo:
    def test_create_model_info(self):
        m = ModelInfo(
            name="test:model", category="general",
            description="A test model", display_name="Test Model"
        )
        assert m.name == "test:model"
        assert m.category == "general"
        assert m.display_name == "Test Model"
