
import os
from typing import List, Tuple, Any
from openhands.core.config import LLMConfig
from openhands.llm.llm import LLM
from openhands.core.message import Message
from openhands.core.metrics import Metrics

class LLMRouter(LLM):
    """LLMRouter class that selects the best LLM for a given query."""

    def __init__(
        self,
        config: LLMConfig,
        metrics: Metrics | None = None,
    ):
        super().__init__(config, metrics)
        self.llm_providers: List[str] = config.llm_providers
        self.notdiamond_api_key = os.environ.get("NOTDIAMOND_API_KEY")
        if not self.notdiamond_api_key:
            raise ValueError("NOTDIAMOND_API_KEY environment variable is not set")

        from notdiamond import NotDiamond
        self.client = NotDiamond()

    def _select_model(self, messages: List[Message]) -> Tuple[str, Any]:
        """Select the best model for the given messages."""
        formatted_messages = [{"role": msg.role, "content": msg.content} for msg in messages]
        session_id, provider = self.client.chat.completions.model_select(
            messages=formatted_messages,
            model=self.llm_providers
        )
        return provider.model, session_id

    def complete(
        self,
        messages: List[Message],
        **kwargs: Any,
    ) -> Tuple[str, float]:
        """Complete the given messages using the best selected model."""
        selected_model, session_id = self._select_model(messages)
        
        # Create a new LLM instance with the selected model
        selected_config = LLMConfig(model=selected_model)
        selected_llm = LLM(config=selected_config, metrics=self.metrics)
        
        # Use the selected LLM to complete the messages
        response, latency = selected_llm.complete(messages, **kwargs)
        
        return response, latency

    def stream(
        self,
        messages: List[Message],
        **kwargs: Any,
    ):
        """Stream the response using the best selected model."""
        selected_model, session_id = self._select_model(messages)
        
        # Create a new LLM instance with the selected model
        selected_config = LLMConfig(model=selected_model)
        selected_llm = LLM(config=selected_config, metrics=self.metrics)
        
        # Use the selected LLM to stream the response
        yield from selected_llm.stream(messages, **kwargs)
