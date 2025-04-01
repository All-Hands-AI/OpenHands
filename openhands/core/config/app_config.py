from typing import ClassVar
from pydantic import Field
from openhands.core import logger
from openhands.core.config.base_config import AppConfig as BaseAppConfig
from openhands.core.config.constants import OH_DEFAULT_AGENT, OH_MAX_ITERATIONS
from openhands.core.config.model_utils import model_defaults_to_dict
from openhands.core.config.llm_config import LLMConfig
from openhands.core.config.agent_config import AgentConfig

class AppConfig(BaseAppConfig):
    """Extended application configuration with additional methods.
    Inherits all fields from BaseAppConfig and adds custom methods.
    """

    default_agent: str = Field(default=OH_DEFAULT_AGENT)

    def get_llm_config(self, name='llm') -> LLMConfig:
        """'llm' is the name for default config (for backward compatibility prior to 0.8)."""
        if name in self.llms:
            return self.llms[name]
        if name is not None and name != 'llm':
            logger.openhands_logger.warning(
                f'llm config group {name} not found, using default config'
            )
        if 'llm' not in self.llms:
            self.llms['llm'] = LLMConfig()
        return self.llms['llm']

    def set_llm_config(self, value: LLMConfig, name='llm') -> None:
        self.llms[name] = value

    def get_agent_config(self, name='agent') -> AgentConfig:
        """'agent' is the name for default config (for backward compatibility prior to 0.8)."""
        if name in self.agents:
            return self.agents[name]
        if 'agent' not in self.agents:
            self.agents['agent'] = AgentConfig()
        return self.agents['agent']

    def set_agent_config(self, value: AgentConfig, name='agent') -> None:
        self.agents[name] = value

    def get_agent_to_llm_config_map(self) -> dict[str, LLMConfig]:
        """Get a map of agent names to llm configs."""
        return {name: self.get_llm_config_from_agent(name) for name in self.agents}

    def get_llm_config_from_agent(self, name='agent') -> LLMConfig:
        agent_config: AgentConfig = self.get_agent_config(name)
        llm_config_name = agent_config.llm_config
        return self.get_llm_config(llm_config_name)

    def get_agent_configs(self) -> dict[str, AgentConfig]:
        return self.agents

    def model_post_init(self, __context):
        """Post-initialization hook, called when the instance is created with only default values."""
        super().model_post_init(__context)
        if not AppConfig.defaults_dict:  # Only set defaults_dict if it's empty
            AppConfig.defaults_dict = model_defaults_to_dict(self)
