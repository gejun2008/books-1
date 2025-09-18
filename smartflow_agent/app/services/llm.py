from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

try:
    from langchain_openai import ChatOpenAI
except ImportError:  # pragma: no cover - optional dependency
    ChatOpenAI = None  # type: ignore

try:
    from langchain_community.chat_models import ChatOllama
except ImportError:  # pragma: no cover - optional dependency
    ChatOllama = None  # type: ignore

from .prompt_templates import RESPONSE_TEMPLATE


class BaseLLMService(ABC):
    """Abstract language model adapter."""

    @abstractmethod
    async def generate_response(self, *, user_input: str, context: dict[str, Any]) -> str:
        """Generate a response for the user input with context."""


class LocalTemplateLLM(BaseLLMService):
    """Deterministic fallback model used for local development without external dependencies."""

    async def generate_response(self, *, user_input: str, context: dict[str, Any]) -> str:
        steps = context.get("plan", [])
        tool_summaries = "\n".join(
            f"- {step.get('tool_name')}({step.get('action')}): {step.get('summary')}" for step in steps
        )
        template = (
            "以下是根据您的请求自动执行的结果:\n"
            f"用户输入: {user_input}\n"
            f"执行计划: {tool_summaries or '无需调用外部系统, 直接提供建议。'}\n"
            "如需进一步操作, 请继续告诉我。"
        )
        return template


class OpenAILLM(BaseLLMService):
    """LLM service backed by OpenAI chat completion models."""

    def __init__(self, *, api_key: str, model: str) -> None:
        if ChatOpenAI is None:  # pragma: no cover - environment guard
            raise RuntimeError("langchain-openai is not installed")
        self._client = ChatOpenAI(api_key=api_key, model=model, temperature=0.1)

    async def generate_response(self, *, user_input: str, context: dict[str, Any]) -> str:
        plan = context.get("plan", [])
        executed_steps = "\n".join(
            f"Step {idx + 1}: {step['tool_name']} -> {step['summary']}"
            for idx, step in enumerate(plan)
        )
        messages = [
            SystemMessage(content=RESPONSE_TEMPLATE),
            HumanMessage(content=user_input),
            AIMessage(content=f"Observed tool outputs:\n{executed_steps}"),
        ]
        response = await self._client.ainvoke(messages)
        return response.content


class OllamaLLM(BaseLLMService):
    """LLM service backed by a locally deployed Ollama server hosting LLaMA models."""

    def __init__(self, *, base_url: str, model: str) -> None:
        if ChatOllama is None:  # pragma: no cover - environment guard
            raise RuntimeError("langchain-community is not installed")
        self._client = ChatOllama(base_url=base_url, model=model, temperature=0.1)

    async def generate_response(self, *, user_input: str, context: dict[str, Any]) -> str:
        plan = context.get("plan", [])
        executed_steps = "\n".join(
            f"Step {idx + 1}: {step['tool_name']} -> {step['summary']}"
            for idx, step in enumerate(plan)
        )
        messages = [
            SystemMessage(content=RESPONSE_TEMPLATE),
            HumanMessage(content=f"User request: {user_input}"),
            AIMessage(content=f"Tool feedback:\n{executed_steps}"),
        ]
        response = await self._client.ainvoke(messages)
        return response.content


def build_llm_service(provider: str, *, settings: Any) -> BaseLLMService:
    provider = provider.lower()
    if provider == "openai":
        if not settings.openai_api_key:
            raise RuntimeError("OpenAI provider selected but SMARTFLOW_OPENAI_API_KEY is not set")
        return OpenAILLM(api_key=settings.openai_api_key, model=settings.openai_model)
    if provider == "ollama":
        return OllamaLLM(base_url=settings.ollama_endpoint, model=settings.ollama_model)
    return LocalTemplateLLM()
