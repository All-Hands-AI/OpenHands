from __future__ import annotations

from pydantic import BaseModel, Field, ValidationError

from openhands.core.config.condenser_config import CondenserConfig, NoOpCondenserConfig
from openhands.core.logger import openhands_logger as logger


class AgentConfig(BaseModel):
    """Configuration for the agent.

    Attributes:
        function_calling: Whether function calling is enabled. Default is True.
        codeact_enable_browsing: Whether browsing delegate is enabled in the action space. Default is False. Only works with function calling.
        codeact_enable_llm_editor: Whether LLM editor is enabled in the action space. Default is False. Only works with function calling.
        codeact_enable_jupyter: Whether Jupyter is enabled in the action space. Default is False.
        llm_config: The name of the llm config to use. If specified, this will override global llm config.
        enable_prompt_extensions: Whether to use prompt extensions (e.g., microagents, inject runtime info). Default is True.
        disabled_microagents: A list of microagents to disable (by name, without .py extension, e.g. ["github", "lint"]). Default is None.
        condenser: Configuration for the memory condenser. Default is NoOpCondenserConfig.
        enable_history_truncation: Whether history should be truncated to continue the session when hitting LLM context length limit.
        enable_som_visual_browsing: Whether to enable SoM (Set of Marks) visual browsing. Default is False.
        a2a_server_url: A list of URLs for the A2A server. Default is an empty list.
    """

    llm_config: str | None = Field(default=None)
    codeact_enable_browsing: bool = Field(default=True)
    codeact_enable_llm_editor: bool = Field(default=False)
    codeact_enable_jupyter: bool = Field(default=True)
    enable_prompt_extensions: bool = Field(default=True)
    disabled_microagents: list[str] = Field(default_factory=list)
    enable_history_truncation: bool = Field(default=True)
    enable_som_visual_browsing: bool = Field(default=True)
    condenser: CondenserConfig = Field(
        default_factory=lambda: NoOpCondenserConfig(type='noop')
    )
    a2a_server_urls: list[str] = Field(default_factory=list)
    enable_llm_router: bool = Field(default=False)
    llm_router_infer_url: str | None = Field(default=None)
    model_config = {'extra': 'forbid'}

    @classmethod
    def from_toml_section(cls, data: dict) -> dict[str, AgentConfig]:
        """
        Create a mapping of AgentConfig instances from a toml dictionary representing the [agent] section.

        The default configuration is built from all non-dict keys in data.
        Then, each key with a dict value is treated as a custom agent configuration, and its values override
        the default configuration.

        Example:
        Apply generic agent config with custom agent overrides, e.g.
            [agent]
            enable_prompt_extensions = false
            [agent.BrowsingAgent]
            enable_prompt_extensions = true
        results in prompt_extensions being true for BrowsingAgent but false for others.

        Returns:
            dict[str, AgentConfig]: A mapping where the key "agent" corresponds to the default configuration
            and additional keys represent custom configurations.
        """

        # Initialize the result mapping
        agent_mapping: dict[str, AgentConfig] = {}

        # Extract base config data (non-dict values)
        base_data = {}
        custom_sections: dict[str, dict] = {}
        for key, value in data.items():
            if isinstance(value, dict):
                custom_sections[key] = value
            else:
                base_data[key] = value

        # Try to create the base config
        try:
            base_config = cls.model_validate(base_data)
            agent_mapping['agent'] = base_config
        except ValidationError as e:
            logger.warning(f'Invalid base agent configuration: {e}. Using defaults.')
            # If base config fails, create a default one
            base_config = cls()
            # Still add it to the mapping
            agent_mapping['agent'] = base_config

        # Process each custom section independently
        for name, overrides in custom_sections.items():
            try:
                # Merge base config with overrides
                merged = {**base_config.model_dump(), **overrides}
                custom_config = cls.model_validate(merged)
                agent_mapping[name] = custom_config
            except ValidationError as e:
                logger.warning(
                    f'Invalid agent configuration for [{name}]: {e}. This section will be skipped.'
                )
                # Skip this custom section but continue with others
                continue

        return agent_mapping
