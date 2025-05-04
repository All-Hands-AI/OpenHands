from openhands.agenthub.codeact_agent.codeact_agent import CodeActAgent
from openhands.core.config.agent_config import AgentConfig
from openhands.llm.llm import LLM
from openhands.memory.condenser.impl.llm_agent_cache_condenser import (
    LLMAgentCacheCondenser,
)


class CustomAgent_CacheCondenser(CodeActAgent):
    def __init__(self, llm: LLM, config: AgentConfig):
        super().__init__(llm, config)
        self.condenser = LLMAgentCacheCondenser(max_size=100, keep_first=10)
