import logging
from copy import deepcopy
from typing import TYPE_CHECKING, cast

from pydantic import SecretStr

# Import MCPConfig directly to avoid circular imports
from openhands.core.config.mcp_config import MCPConfig

logger = logging.getLogger(__name__)

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
        for (
            settings_field,
            config_field,
            nested_obj,
        ) in ConfigurationMerger.FIELD_MAPPING:
            # Get the value from settings
            settings_value = getattr(settings, settings_field, None)

            # Skip if the settings value is None
            if settings_value is None:
                continue

            # Apply the value to the appropriate config object
            if nested_obj is None:
                # Apply to the main config object
                logger.debug(
                    f'Merging setting {settings_field} -> config.{config_field}'
                )
                setattr(config, config_field, settings_value)
            elif nested_obj == 'llm_config':
                # Apply to the LLM config
                logger.debug(
                    f'Merging setting {settings_field} -> config.llm_config.{config_field}'
                )
                setattr(llm_config, config_field, settings_value)
            elif nested_obj == 'security':
                # Apply to the security config
                logger.debug(
                    f'Merging setting {settings_field} -> config.security.{config_field}'
                )
                setattr(config.security, config_field, settings_value)
            elif nested_obj == 'sandbox':
                # Apply to the sandbox config
                logger.debug(
                    f'Merging setting {settings_field} -> config.sandbox.{config_field}'
                )
                setattr(config.sandbox, config_field, settings_value)
            else:
                # Unsupported nested object
                raise ValueError(
                    f"Unsupported nested_obj '{nested_obj}' for field mapping: "
                    f'({settings_field}, {config_field}, {nested_obj})'
                )

        # MCP settings need special handling for merging
        ConfigurationMerger._merge_mcp_settings(config, settings)

    @staticmethod
    def _merge_mcp_settings(config: 'OpenHandsConfig', settings: 'Settings') -> None:
        """Merge MCP-specific settings."""
        if settings.mcp_config is None:
            logger.debug('No MCP config in settings, skipping MCP merge')
            return

        # Check if config has any MCP servers configured
        # Note: config.mcp should never be None in normal usage (it has a default_factory),
        # but tests may set it to None, so we handle both cases
        mcp_config = cast('MCPConfig | None', config.mcp)
        if mcp_config is None:
            config_has_servers = False
        else:
            config_has_servers = bool(
                mcp_config.sse_servers
                or mcp_config.stdio_servers
                or mcp_config.shttp_servers
            )

        if not config_has_servers:
            logger.debug('No MCP servers in config, using settings MCP config directly')
            config.mcp = settings.mcp_config
            return

        logger.debug('Merging MCP configs with config servers taking precedence')

        # Merge MCP configs with config.toml taking priority (appearing first)
        merged_mcp = MCPConfig(
            sse_servers=list(config.mcp.sse_servers)
            + list(settings.mcp_config.sse_servers),
            stdio_servers=list(config.mcp.stdio_servers)
            + list(settings.mcp_config.stdio_servers),
            shttp_servers=list(config.mcp.shttp_servers)
            + list(settings.mcp_config.shttp_servers),
        )

        logger.debug(
            f'Merged MCP config has {len(merged_mcp.sse_servers)} SSE servers, '
            f'{len(merged_mcp.stdio_servers)} stdio servers, and '
            f'{len(merged_mcp.shttp_servers)} shttp servers'
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

        # Create a new Settings object with default values
        settings = Settings(language='en')

        # Get config objects that will be accessed frequently
        llm_config = config.get_llm_config()

        # Use the field mapping to apply config values to settings
        for (
            settings_field,
            config_field,
            nested_obj,
        ) in ConfigurationMerger.FIELD_MAPPING:
            # Get the value from the appropriate config object
            if nested_obj is None:
                config_value = getattr(config, config_field, None)
                logger.debug(
                    f'Converting config.{config_field} -> settings.{settings_field}'
                )
            elif nested_obj == 'llm_config':
                config_value = getattr(llm_config, config_field, None)
                logger.debug(
                    f'Converting config.llm_config.{config_field} -> settings.{settings_field}'
                )
            elif nested_obj == 'security':
                config_value = getattr(config.security, config_field, None)
                logger.debug(
                    f'Converting config.security.{config_field} -> settings.{settings_field}'
                )
            elif nested_obj == 'sandbox':
                config_value = getattr(config.sandbox, config_field, None)
                logger.debug(
                    f'Converting config.sandbox.{config_field} -> settings.{settings_field}'
                )
            else:
                # Unsupported nested object
                raise ValueError(
                    f"Unsupported nested_obj '{nested_obj}' for field mapping: "
                    f'({settings_field}, {config_field}, {nested_obj})'
                )

            # Skip if the config value is None
            if config_value is None:
                continue

            # Handle special cases for API keys (convert to SecretStr)
            if settings_field in ('llm_api_key', 'sandbox_api_key', 'search_api_key'):
                if isinstance(config_value, str):
                    logger.debug(
                        f'Converting string API key to SecretStr for {settings_field}'
                    )
                    setattr(settings, settings_field, SecretStr(config_value))
                elif hasattr(config_value, 'get_secret_value'):
                    # It's already a SecretStr
                    setattr(settings, settings_field, config_value)
                else:
                    # Skip mock objects or other non-string types
                    logger.debug(f'Skipping non-string API key for {settings_field}')
            else:
                # Apply the value directly
                setattr(settings, settings_field, config_value)

        # Special handling for MCP config
        if hasattr(config, 'mcp') and config.mcp is not None:
            logger.debug('Adding MCP config to settings')
            settings.mcp_config = config.mcp

        return settings
