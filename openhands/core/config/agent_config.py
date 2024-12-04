from dataclasses import dataclass, field, fields

from openhands.core.config.condenser_config import CondenserConfig, NoOpCondenserConfig
from openhands.core.config.config_utils import get_field_info


@dataclass
class AgentConfig:
    """Configuration for the agent.

    Attributes:
        function_calling: Whether function calling is enabled. Default is True.
        codeact_enable_browsing: Whether browsing delegate is enabled in the action space. Default is False. Only works with function calling.
        codeact_enable_llm_editor: Whether LLM editor is enabled in the action space. Default is False. Only works with function calling.
        codeact_enable_jupyter: Whether Jupyter is enabled in the action space. Default is False.
        micro_agent_name: The name of the micro agent to use for this agent.
        memory_enabled: Whether long-term memory (embeddings) is enabled.
        memory_max_threads: The maximum number of threads indexing at the same time for embeddings.
        llm_config: The name of the llm config to use. If specified, this will override global llm config.
        use_microagents: Whether to use microagents at all. Default is True.
        disabled_microagents: A list of microagents to disable. Default is None.
        condenser: Configuration for the memory condenser. Default is NoOpCondenserConfig.
    """

    codeact_enable_browsing: bool = True
    codeact_enable_llm_editor: bool = False
    codeact_enable_jupyter: bool = True
    micro_agent_name: str | None = None
    memory_enabled: bool = False
    memory_max_threads: int = 3
    llm_config: str | None = None
    use_microagents: bool = True
    disabled_microagents: list[str] | None = None
    condenser: CondenserConfig = field(default_factory=NoOpCondenserConfig)  # type: ignore

    def defaults_to_dict(self) -> dict:
        """Serialize fields to a dict for the frontend, including type hints, defaults, and whether it's optional."""
        result = {}
        for f in fields(self):
            result[f.name] = get_field_info(f)
        return result
