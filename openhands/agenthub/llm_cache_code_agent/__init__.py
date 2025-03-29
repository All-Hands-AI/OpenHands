from openhands.agenthub.llm_cache_code_agent.llm_cache_code_agent import (
    LLMCacheCodeAgent,
)
from openhands.controller.agent import Agent

Agent.register('LLMCacheCodeAgent', LLMCacheCodeAgent)
