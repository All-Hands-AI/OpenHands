from __future__ import annotations

from typing import Type

from openhands.agenthub.codeact_agent.codeact_agent import CodeActAgent
from openhands.core.config.agent_config import AgentConfig
from openhands.llm import LLM
from openhands.memory.condenser.condenser import Condenser
from openhands.memory.condenser.impl.llm_agent_cache_condenser import (
    LLMAgentCacheCondenser,
)


class LLMCacheCodeAgent(CodeActAgent):
    """A CodeActAgent that uses a specialized condenser to take advantage of LLM caching.

    This agent uses the LLMAgentCacheCondenser, which shares the same LLM instance as the agent.
    This allows for effective caching of prompts between the agent and condenser.

    The condenser uses the same prompt format as the agent and appends condensation instructions
    at the end. This allows the LLM to take advantage of the cached prompt and only process the
    new instructions, significantly reducing token usage and costs.
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
        # Create and set the LLMAgentCacheCondenser, passing self as the agent
        self.condenser = LLMAgentCacheCondenser(agent=self)

    @classmethod
    def get_condenser_class(cls) -> Type[Condenser]:
        """Get the condenser class used by this agent.

        Returns:
            The LLMAgentCacheCondenser class.
        """
        return LLMAgentCacheCondenser
