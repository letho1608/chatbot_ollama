from typing import Any
import math


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
        result = eval(expression, {'__builtins__': {}}, allowed_names)
        return str(result)
    except Exception as exc:
        return f"Calculator error: {exc}"


def echo(message: str) -> str:
    return message.strip()


def search(query: str) -> str:
    return f"Search result for '{query}': (simulated response)"
