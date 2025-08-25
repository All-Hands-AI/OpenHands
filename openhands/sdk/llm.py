from __future__ import annotations

from typing import Any

from pydantic import BaseModel, SecretStr

from openhands.core.config import LLMConfig as CoreLLMConfig
from openhands.llm.llm import LLM as CoreLLM


class LLMConfig(BaseModel):
    model: str
    api_key: str | None = None
    base_url: str | None = None
    api_version: str | None = None
    custom_llm_provider: str | None = None
    temperature: float = 0.0
    reasoning_effort: str | None = None
    max_output_tokens: int | None = None
    top_k: int | None = None
    top_p: float | None = None


class LLM:
    def __init__(self, config: LLMConfig):
        # Map to CoreLLMConfig
        core = CoreLLMConfig(
            model=config.model,
            api_key=SecretStr(config.api_key) if config.api_key else None,
            base_url=config.base_url,
            api_version=config.api_version,
            custom_llm_provider=config.custom_llm_provider,
            temperature=config.temperature,
            max_output_tokens=config.max_output_tokens,
            top_k=config.top_k,
            top_p=config.top_p if config.top_p is not None else 1.0,
            reasoning_effort=config.reasoning_effort,
        )
        # service_id is arbitrary for SDK; use 'sdk'
        self._core = CoreLLM(core, service_id='sdk')

    def supports_function_calling(self) -> bool:
        try:
            return self._core.is_function_calling_active()
        except Exception:
            return False

    def send(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict],
        tool_choice: str = 'auto',
    ) -> dict:
        # Core LLM expects openai-like dicts; we pass through with tool_choice
        if tools and not self.supports_function_calling():
            # Friendly warning path; do not block
            from openhands.core.logger import openhands_logger as logger

            logger.warning(
                'LLM may not support function calling; proceeding anyway (tool_choice=auto).'
            )
        response = self._core.completion(
            messages=messages, tools=tools, tool_choice=tool_choice
        )
        return response
