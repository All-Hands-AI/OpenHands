from dataclasses import dataclass, fields

from openhands.core.config.config_utils import get_field_info


@dataclass
class AgentConfig:
    """Configuration for the agent.

    Attributes:
        micro_agent_name: The name of the micro agent to use for this agent.
        memory_enabled: Whether long-term memory (embeddings) is enabled.
        memory_max_threads: The maximum number of threads indexing at the same time for embeddings.
        llm_config: The name of the llm config to use. If specified, this will override global llm config.
    """

    micro_agent_name: str | None = None
    memory_enabled: bool = False
    memory_max_threads: int = 3
    llm_config: str | None = None

    def defaults_to_dict(self) -> dict:
        """Serialize fields to a dict for the frontend, including type hints, defaults, and whether it's optional."""
        result = {}
        for f in fields(self):
            result[f.name] = get_field_info(f)
        return result
