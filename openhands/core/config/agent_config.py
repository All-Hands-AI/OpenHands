from pydantic import BaseModel, Field

from openhands.core.config.condenser_config import CondenserConfig, NoOpCondenserConfig


class AgentConfig(BaseModel):
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
        enable_prompt_extensions: Whether to use prompt extensions (e.g., microagents, inject runtime info). Default is True.
        disabled_microagents: A list of microagents to disable. Default is None.
        condenser: Configuration for the memory condenser. Default is NoOpCondenserConfig.
        enable_history_truncation: If history should be truncated once LLM context limit is hit.
    """

    codeact_enable_browsing: bool = Field(default=True)
    enable_som_visual_browsing: bool = Field(default=False)
    codeact_enable_llm_editor: bool = Field(default=False)
    codeact_enable_jupyter: bool = Field(default=True)
    micro_agent_name: str | None = Field(default=None)
    memory_enabled: bool = Field(default=False)
    memory_max_threads: int = Field(default=3)
    llm_config: str | None = Field(default=None)
    enable_prompt_extensions: bool = Field(default=True)
    disabled_microagents: list[str] | None = Field(default=None)
    condenser: CondenserConfig = Field(default_factory=NoOpCondenserConfig)
    enable_history_truncation: bool = Field(default=True)
