import os
import pathlib
import sys
from dotenv import load_dotenv

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.agent.agent import ReActAgent
from src.agent.tools import calculator, echo, search
from src.core.local_provider import LocalProvider
from src.core.openai_provider import OpenAIProvider
from src.core.gemini_provider import GeminiProvider


def build_provider():
    provider_name = os.getenv("DEFAULT_PROVIDER", "openai").lower()
    if provider_name == "local":
        model_path = os.getenv("LOCAL_MODEL_PATH", "./models/Phi-3-mini-4k-instruct-q4.gguf")
        return LocalProvider(model_path=model_path)
    if provider_name == "google":
        api_key = os.getenv("GEMINI_API_KEY")
        return GeminiProvider(api_key=api_key)
    return OpenAIProvider(api_key=os.getenv("OPENAI_API_KEY"))


def build_tools():
    return [
        {
            "name": "calculator",
            "description": "Evaluate a math expression and return the numeric result.",
            "func": calculator,
        },
        {
            "name": "search",
            "description": "Search a query and return a short simulated summary.",
            "func": search,
        },
        {
            "name": "echo",
            "description": "Repeat back the provided text.",
            "func": echo,
        },
    ]


def main():
    load_dotenv()
    provider = build_provider()
    tools = build_tools()
    agent = ReActAgent(provider, tools)

    print("=== ReAct Agent Runner ===")
    prompt = input("User prompt: ")
    answer = agent.run(prompt)

    print("\n=== Agent Output ===")
    print(answer)


if __name__ == "__main__":
    main()
