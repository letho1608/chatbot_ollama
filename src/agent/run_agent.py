import argparse
import os
import pathlib
import sys
from dotenv import load_dotenv

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.agent.agent import ReActAgent
from src.agent.baseline import ChatbotBaseline
from src.agent.tools import calculator, echo, search, dataset_search
from src.core.openai_provider import OpenAIProvider
from src.core.gemini_provider import GeminiProvider


def build_provider():
    provider_name = os.getenv("DEFAULT_PROVIDER", "openai").lower()
    if provider_name == "local":
        try:
            from src.core.local_provider import LocalProvider
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "Local provider requires llama-cpp-python. Install it or switch DEFAULT_PROVIDER to openai/google."
            ) from exc

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
            "name": "dataset_search",
            "description": "Search the local dataset for matching text lines.",
            "func": dataset_search,
        },
        {
            "name": "echo",
            "description": "Repeat back the provided text.",
            "func": echo,
        },
    ]


def parse_args():
    parser = argparse.ArgumentParser(description="Run the Chatbot or ReAct agent.")
    parser.add_argument(
        "--mode",
        choices=["agent", "baseline"],
        default="agent",
        help="Choose whether to run the ReAct agent or the baseline chatbot.",
    )
    return parser.parse_args()


def run_agent(provider):
    tools = build_tools()
    agent = ReActAgent(provider, tools)

    print("=== ReAct Agent Runner ===")
    print("Type 'quit' or 'exit' to stop.")

    while True:
        prompt = input("User prompt: ")
        if prompt.strip().lower() in {"quit", "exit"}:
            print("Goodbye!")
            break

        answer = agent.run(prompt)
        print("\n=== Agent Output ===")
        print(answer)
        print("\n---\n")


def run_baseline(provider):
    baseline = ChatbotBaseline(provider)

    print("=== Baseline Chatbot Runner ===")
    print("Type 'quit' or 'exit' to stop.")

    while True:
        prompt = input("User prompt: ")
        if prompt.strip().lower() in {"quit", "exit"}:
            print("Goodbye!")
            break

        answer = baseline.run(prompt)
        print("\n=== Chatbot Output ===")
        print(answer)
        print("\n---\n")


def main():
    args = parse_args()
    load_dotenv()
    provider = build_provider()

    if args.mode == "baseline":
        run_baseline(provider)
    else:
        run_agent(provider)


if __name__ == "__main__":
    main()
