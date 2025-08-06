from copy import deepcopy
from typing import TYPE_CHECKING

from pydantic import SecretStr

# Import MCPConfig directly to avoid circular imports
from openhands.core.config.mcp_config import MCPConfig

if TYPE_CHECKING:
    from openhands.core.config.openhands_config import OpenHandsConfig
    from openhands.storage.data_models.settings import Settings


class ConfigurationMerger:
    """Utility class for merging Settings with OpenHandsConfig."""
    
    # Mapping between Settings fields and OpenHandsConfig fields
    # Format: (settings_field, config_field, config_nested_object)
    FIELD_MAPPING = [
        # Core settings
        ('agent', 'default_agent', None),
        ('max_iterations', 'max_iterations', None),
        ('max_budget_per_task', 'max_budget_per_task', None),
        ('git_user_name', 'git_user_name', None),
        ('git_user_email', 'git_user_email', None),
        ('search_api_key', 'search_api_key', None),
        
        # LLM settings
        ('llm_model', 'model', 'llm_config'),
        ('llm_api_key', 'api_key', 'llm_config'),
        ('llm_base_url', 'base_url', 'llm_config'),
        
        # Security settings
        ('security_analyzer', 'security_analyzer', 'security'),
        ('confirmation_mode', 'confirmation_mode', 'security'),
        
        # Sandbox settings
        ('remote_runtime_resource_factor', 'remote_runtime_resource_factor', 'sandbox'),
        ('sandbox_base_container_image', 'base_container_image', 'sandbox'),
        ('sandbox_runtime_container_image', 'runtime_container_image', 'sandbox'),
        ('sandbox_api_key', 'api_key', 'sandbox'),
    ]

    """
    This class provides a centralized way to merge user settings with the
    application configuration, ensuring consistent precedence rules across
    all configuration types.
    """

    @staticmethod
    def merge_settings_with_config(
        settings: 'Settings', config: 'OpenHandsConfig'
    ) -> 'OpenHandsConfig':
        """Merge user settings with application configuration.

        Creates a new config object with settings applied according to
        consistent precedence rules. Settings generally take precedence
        over config values, except for MCP settings which are merged.

        Args:
            settings: User settings to apply
            config: Base configuration to merge with

        Returns:
            A new OpenHandsConfig instance with settings applied
        """
        # Create a deep copy to avoid modifying the original
        merged_config = deepcopy(config)

        # Apply settings to config with clear precedence rules
        ConfigurationMerger._merge_settings(merged_config, settings)

        return merged_config

    @staticmethod
    def _merge_settings(config: 'OpenHandsConfig', settings: 'Settings') -> None:
        """Apply settings to config with consistent precedence rules."""
        # Get LLM config once to avoid repeated calls
        llm_config = config.get_llm_config()
        
        # Use the field mapping to apply settings to config
        for settings_field, config_field, nested_obj in ConfigurationMerger.FIELD_MAPPING:
            # Get the value from settings
            settings_value = getattr(settings, settings_field, None)
            
            # Skip if the settings value is None
            if settings_value is None:
                continue
                
            # Apply the value to the appropriate config object
            if nested_obj is None:
                # Apply to the main config object
                setattr(config, config_field, settings_value)
            elif nested_obj == 'llm_config':
                # Apply to the LLM config
                setattr(llm_config, config_field, settings_value)
            elif nested_obj == 'security':
                # Apply to the security config
                setattr(config.security, config_field, settings_value)
            elif nested_obj == 'sandbox':
                # Apply to the sandbox config
                setattr(config.sandbox, config_field, settings_value)
        
        # MCP settings need special handling for merging
        ConfigurationMerger._merge_mcp_settings(config, settings)

    # The _merge_core_settings method has been replaced by the field mapping approach

    # The _merge_llm_settings method has been replaced by the field mapping approach

    # The _merge_security_settings method has been replaced by the field mapping approach

    # The _merge_sandbox_settings method has been replaced by the field mapping approach

    @staticmethod
    def _merge_mcp_settings(config: 'OpenHandsConfig', settings: 'Settings') -> None:
        """Merge MCP-specific settings."""
        if settings.mcp_config is None:
            return

        if config.mcp is None:
            # mypy doesn't understand that this is reachable
            config.mcp = settings.mcp_config  # type: ignore
            return

        # Merge MCP configs with config.toml taking priority (appearing first)

        merged_mcp = MCPConfig(
            sse_servers=list(config.mcp.sse_servers)
            + list(settings.mcp_config.sse_servers),
            stdio_servers=list(config.mcp.stdio_servers)
            + list(settings.mcp_config.stdio_servers),
            shttp_servers=list(config.mcp.shttp_servers)
            + list(settings.mcp_config.shttp_servers),
        )

        config.mcp = merged_mcp

    @staticmethod
    def config_to_settings(config: 'OpenHandsConfig') -> 'Settings':
        """Convert an OpenHandsConfig to a Settings object.

        This method creates a new Settings object with values from the provided
        OpenHandsConfig. It's the inverse operation of merge_settings_with_config.

        Args:
            config: The configuration to convert

        Returns:
            A new Settings instance with values from the config
        """
        # Import here to avoid circular imports
        from openhands.storage.data_models.settings import Settings

        llm_config = config.get_llm_config()
        security = config.security

        # Get MCP config if available
        mcp_config = None
        if hasattr(config, 'mcp') and config.mcp is not None:
            mcp_config = config.mcp

        # Convert API key to SecretStr if it's a string
        llm_api_key = None
        if llm_config.api_key is not None:
            if isinstance(llm_config.api_key, str):
                llm_api_key = SecretStr(llm_config.api_key)
            elif hasattr(llm_config.api_key, 'get_secret_value'):
                # It's already a SecretStr
                llm_api_key = llm_config.api_key
            else:
                # Skip mock objects or other non-string types
                llm_api_key = None

        # Convert sandbox API key to SecretStr if it's a string
        sandbox_api_key = None
        if config.sandbox.api_key is not None:
            if isinstance(config.sandbox.api_key, str):
                sandbox_api_key = SecretStr(config.sandbox.api_key)
            elif hasattr(config.sandbox.api_key, 'get_secret_value'):
                # It's already a SecretStr
                sandbox_api_key = config.sandbox.api_key
            else:
                # Skip mock objects or other non-string types
                sandbox_api_key = None

        # Convert search API key to SecretStr if it's a string
        search_api_key = None
        if config.search_api_key is not None:
            if isinstance(config.search_api_key, str):
                search_api_key = SecretStr(config.search_api_key)
            elif hasattr(config.search_api_key, 'get_secret_value'):
                # It's already a SecretStr
                search_api_key = config.search_api_key
            else:
                # Skip mock objects or other non-string types
                search_api_key = None

        # Handle base_url for mocks
        llm_base_url = None
        if llm_config.base_url is not None:
            if isinstance(llm_config.base_url, str):
                llm_base_url = llm_config.base_url
            else:
                # Skip mock objects or other non-string types
                llm_base_url = None
                
        settings = Settings(
            language='en',
            agent=config.default_agent,
            max_iterations=config.max_iterations,
            security_analyzer=security.security_analyzer,
            confirmation_mode=security.confirmation_mode,
            llm_model=llm_config.model,
            llm_api_key=llm_api_key,
            llm_base_url=llm_base_url,
            remote_runtime_resource_factor=config.sandbox.remote_runtime_resource_factor,
            sandbox_base_container_image=config.sandbox.base_container_image,
            sandbox_runtime_container_image=config.sandbox.runtime_container_image,
            sandbox_api_key=sandbox_api_key,
            mcp_config=mcp_config,
            search_api_key=search_api_key,
            max_budget_per_task=config.max_budget_per_task,
            git_user_name=config.git_user_name,
            git_user_email=config.git_user_email,
        )
        return settings
