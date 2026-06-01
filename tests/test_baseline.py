import os
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.agent.baseline import ChatbotBaseline
from src.core.llm_provider import LLMProvider


class DummyProvider(LLMProvider):
    def __init__(self, response):
        super().__init__(model_name="dummy")
        self.response = response

    def generate(self, prompt: str, system_prompt=None):
        return {
            "content": self.response,
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            "latency_ms": 0,
            "provider": "dummy",
        }

    def stream(self, prompt: str, system_prompt=None):
        yield self.response


def test_baseline_returns_direct_answer():
    provider = DummyProvider("This is the baseline answer.")
    baseline = ChatbotBaseline(provider)
    result = baseline.run("What is the meaning of life?")

    assert "baseline answer" in result
