from __future__ import annotations

from typing import Any, Optional

from openhands.agenthub.agent_interface import LLMCompletionProvider
from openhands.agenthub.codeact_agent.codeact_agent import CodeActAgent
from openhands.core.config.agent_config import AgentConfig
from openhands.llm import LLM
from openhands.memory.condenser.condenser import Condenser


class LLMCacheCodeAgent(CodeActAgent, LLMCompletionProvider):
    """A CodeActAgent that uses a specialized condenser to take advantage of LLM caching.

    This agent uses a condenser that shares the same LLM instance as the agent.
    This allows for effective caching of prompts between the agent and condenser.

    The condenser uses the same prompt format as the agent and appends condensation instructions
    at the end. This allows the LLM to take advantage of the cached prompt and only process the
    new instructions, significantly reducing token usage and costs.

    This agent implements the LLMCompletionProvider interface to expose its LLM call generation
    details to the condenser.
    """

    def __init__(
        self,
        llm: LLM,
        config: AgentConfig,
    ) -> None:
        """Initialize the agent with the given LLM and configuration.

        Args:
            llm: The LLM to use for generating responses.
            config: The agent configuration.
        """
        # Initialize the parent class
        super().__init__(llm=llm, config=config)

        # Ensure conversation_memory and prompt_manager are not None
        if self.conversation_memory is None or self.prompt_manager is None:
            raise ValueError(
                'LLMCacheCodeAgent: conversation_memory and prompt_manager must not be None.'
            )

        # Override the condenser created by the parent class
        # We'll create the condenser after the agent is fully initialized
        self._condenser: Optional[Any] = None

    @property
    def condenser(self) -> Condenser:
        """Get the condenser for this agent.

        This lazy-loads the condenser to avoid circular dependencies.

        Returns:
            The condenser instance
        """
        if self._condenser is None:
            # Import here to avoid circular imports
            from openhands.memory.condenser.impl.llm_agent_cache_condenser import (
                LLMAgentCacheCondenser,
            )

            self._condenser = LLMAgentCacheCondenser(
                max_size=100, trigger_word='CONDENSE!'
            )
        return self._condenser

    @condenser.setter
    def condenser(self, value: Condenser) -> None:
        """Set the condenser for this agent.

        Args:
            value: The condenser to use
        """
        self._condenser = value
