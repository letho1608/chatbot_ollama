from typing import Optional
from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger

class ChatbotBaseline:
    """
    A minimal chatbot baseline that answers the user directly without tool calls.
    """

    def __init__(self, llm: LLMProvider):
        self.llm = llm

    def get_system_prompt(self) -> str:
        return (
            "You are a helpful assistant. Answer the user's question directly and clearly. "
            "Do not attempt to use tools or reference a tool-based process."
        )

    def run(self, user_input: str) -> str:
        logger.log_event("BASELINE_START", {"input": user_input, "model": self.llm.model_name})
        result = self.llm.generate(user_input, system_prompt=self.get_system_prompt())
        text = result.get("content", "").strip()
        logger.log_event("BASELINE_RESPONSE", {"response": text})
        return text if text else "No answer returned from the baseline chatbot."
