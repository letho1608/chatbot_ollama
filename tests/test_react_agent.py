import os
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.agent.agent import ReActAgent
from src.core.llm_provider import LLMProvider


class DummyProvider(LLMProvider):
    def __init__(self, responses):
        super().__init__(model_name="dummy")
        self.responses = responses
        self.index = 0

    def generate(self, prompt: str, system_prompt=None):
        content = self.responses[self.index]
        self.index = min(self.index + 1, len(self.responses) - 1)
        return {
            "content": content,
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            "latency_ms": 0,
            "provider": "dummy",
        }

    def stream(self, prompt: str, system_prompt=None):
        yield self.generate(prompt, system_prompt=system_prompt)["content"]


def calculator(expression: str) -> str:
    return str(eval(expression, {"__builtins__": {}}, {}))


def test_react_agent_executes_tool_and_returns_final_answer():
    provider = DummyProvider([
        "Thought: I should calculate the sum. Action: calculator(2+2)",
        "Thought: I have the answer. Final Answer: 4",
    ])
    tools = [
        {"name": "calculator", "description": "Adds numbers.", "func": calculator},
    ]
    agent = ReActAgent(provider, tools)

    result = agent.run("What is 2 plus 2?")

    assert "4" in result


def test_react_agent_returns_direct_final_answer():
    provider = DummyProvider([
        "Thought: I know the answer. Final Answer: 42",
    ])
    agent = ReActAgent(provider, [])

    result = agent.run("What is the meaning of life?")

    assert "42" in result
