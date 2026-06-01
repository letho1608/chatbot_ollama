import math
import pathlib
from typing import Any

DATASET_PATH = pathlib.Path(__file__).resolve().parents[2] / "dataset.txt"


def calculator(expression: str) -> str:
    """Evaluate a simple arithmetic expression safely."""
    try:
        allowed_names = {
            k: getattr(math, k)
            for k in [
                'acos', 'asin', 'atan', 'atan2', 'ceil', 'cos', 'cosh', 'degrees',
                'e', 'exp', 'fabs', 'floor', 'fmod', 'hypot', 'log', 'log10',
                'pi', 'pow', 'radians', 'sin', 'sinh', 'sqrt', 'tan', 'tanh'
            ]
        }
        allowed_names.update({'abs': abs, 'round': round, 'min': min, 'max': max})
        expression = expression.strip()
        result = eval(expression, {'__builtins__': {}}, allowed_names)
        return str(result)
    except Exception as exc:
        return f"Calculator error: {exc}"


def echo(message: str) -> str:
    return message.strip()


def search(query: str) -> str:
    return f"Search result for '{query}': This is a simulated knowledge search."


def dataset_search(query: str) -> str:
    if not DATASET_PATH.exists():
        return "Dataset search unavailable: dataset.txt not found."

    results = []
    query_lower = query.lower()
    with open(DATASET_PATH, encoding="utf-8", errors="ignore") as data_file:
        for line in data_file:
            if query_lower in line.lower():
                results.append(line.strip())
                if len(results) >= 5:
                    break

    if not results:
        return f"No dataset matches found for '{query}'."
    return " | ".join(results)
