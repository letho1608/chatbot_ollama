import ast
import re
from typing import List, Dict, Any, Optional
from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger

class ReActAgent:
    """
    A ReAct-style Agent that follows the Thought-Action-Observation loop.
    """

    def __init__(self, llm: LLMProvider, tools: List[Dict[str, Any]], max_steps: int = 5):
        self.llm = llm
        self.tools = tools
        self.max_steps = max_steps
        self.history: List[str] = []

    def get_system_prompt(self) -> str:
        tool_descriptions = "\n".join([f"- {t['name']}: {t['description']}" for t in self.tools])
        return f"""
You are an intelligent assistant. You have access to the following tools:
{tool_descriptions}

Follow this ReAct format exactly:
Thought: your reasoning about the next step.
Action: tool_name(argument1, argument2, ...)
Observation: result from the tool.
... (repeat Thought/Action/Observation as needed)
Final Answer: your final response to the user.
"""

    def run(self, user_input: str) -> str:
        logger.log_event("AGENT_START", {"input": user_input, "model": self.llm.model_name})
        self.history = []
        steps = 0

        while steps < self.max_steps:
            current_prompt = self._build_prompt(user_input)
            result = self.llm.generate(current_prompt, system_prompt=self.get_system_prompt())
            response_text = result.get("content", "").strip()
            logger.log_event("LLM_RESPONSE", {"step": steps + 1, "response": response_text})

            if not response_text:
                break

            self.history.append(response_text)

            final_answer = self._extract_final_answer(response_text)
            if final_answer:
                logger.log_event("AGENT_FINAL_ANSWER", {"answer": final_answer, "steps": steps + 1})
                return final_answer

            action = self._parse_action(response_text)
            if action:
                tool_output = self._execute_tool(action["tool"], action["args"])
                observation = f"Observation: {tool_output}"
                self.history.append(observation)
                logger.log_event("AGENT_ACTION", {"tool": action["tool"], "args": action["args"], "output": tool_output})
                steps += 1
                continue

            # If no action is found, treat the response as the final answer.
            logger.log_event("AGENT_FALLBACK_ANSWER", {"response": response_text})
            return response_text

        logger.log_event("AGENT_END", {"steps": steps})
        return "I could not produce a final answer within the allowed number of steps."

    def _build_prompt(self, user_input: str) -> str:
        if not self.history:
            return user_input
        return user_input + "\n\n" + "\n".join(self.history)

    def _extract_final_answer(self, text: str) -> Optional[str]:
        match = re.search(r"Final Answer:\s*(.+)$", text, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()
        return None

    def _parse_action(self, text: str) -> Optional[Dict[str, str]]:
        match = re.search(r"Action:\s*([a-zA-Z0-9_\-]+)\((.*)\)", text, re.IGNORECASE | re.DOTALL)
        if not match:
            return None

        tool_name = match.group(1).strip()
        raw_args = match.group(2).strip()
        parsed_args = self._parse_args(raw_args)
        return {"tool": tool_name, "args": parsed_args}

    def _parse_args(self, args: str) -> List[Any]:
        if not args:
            return []

        try:
            parsed = ast.literal_eval(f"({args},)")
            if isinstance(parsed, tuple) and len(parsed) == 1:
                return [parsed[0]]
            return list(parsed)
        except Exception:
            # Fallback: split by comma and strip whitespace
            return [item.strip().strip('"\'') for item in args.split(",") if item.strip()]

    def _execute_tool(self, tool_name: str, args: List[Any]) -> str:
        for tool in self.tools:
            if tool["name"] == tool_name:
                func = tool.get("func")
                if callable(func):
                    try:
                        return func(*args)
                    except Exception as exc:
                        return f"Tool execution failed: {exc}"
                return f"Tool {tool_name} has no callable function."
        return f"Tool {tool_name} not found."
