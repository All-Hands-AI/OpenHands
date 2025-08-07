# Configuration Management in OpenHands

## Overview

OpenHands uses a flexible configuration system that allows settings to be defined through environment variables, TOML files, command-line arguments, and user settings. The configuration is managed through a package structure in `openhands/core/config/`.

## Configuration Sources and Precedence

OpenHands configuration comes from multiple sources, with the following precedence (highest to lowest):

1. **Command-line Arguments**: Settings provided as command-line arguments
2. **User Settings**: Settings configured by users through the UI or API
3. **Environment Variables**: Settings defined in the environment
4. **TOML Files**: Settings defined in `config.toml`
5. **Default Values**: Default values defined in the configuration classes

## Configuration Classes

The main configuration classes are:

- `OpenHandsConfig`: The root configuration class (formerly AppConfig)
- `LLMConfig`: Configuration for the Language Model
- `AgentConfig`: Configuration for the agent
- `SandboxConfig`: Configuration for the sandbox environment
- `SecurityConfig`: Configuration for security settings
- `MCPConfig`: Configuration for Model Context Protocol

These classes are defined as dataclasses, with class attributes holding default values for all fields.

## Loading Configuration from Environment Variables

The `load_from_env` function in the config package is responsible for loading configuration values from environment variables. It recursively processes the configuration classes, mapping environment variable names to class attributes.

### Naming Convention for Environment Variables

- Prefix: uppercase name of the configuration class followed by an underscore (e.g., `LLM_`, `AGENT_`)
- Field Names: all uppercase
- Full Variable Name: Prefix + Field Name (e.g., `LLM_API_KEY`, `AGENT_MEMORY_ENABLED`)

### Examples

```bash
export LLM_API_KEY='your_api_key_here'
export LLM_MODEL='gpt-4'
export AGENT_MEMORY_ENABLED='true'
export SANDBOX_TIMEOUT='300'
```

## Type Handling

The `load_from_env` function attempts to cast environment variable values to the types specified in the models. It handles:

- Basic types (str, int, bool)
- Optional types (e.g., `str | None`)
- Nested models

If type casting fails, an error is logged, and the default value is retained.

## Default Values

If an environment variable is not set, the default value specified in the model is used.

## Security Considerations

Be cautious when setting sensitive information like API keys in environment variables. Ensure your environment is secure.

## Usage

The `load_openhands_config()` function is the recommended way to initialize your configuration. It performs the following steps:

1. Creates an instance of `OpenHandsConfig` with default values
2. Loads settings from the `config.toml` file (if present)
3. Loads settings from environment variables, overriding TOML settings
4. Processes command-line arguments, which have the highest precedence and override all other sources
5. Applies final tweaks and validations to the configuration
6. Optionally sets global logging levels based on the configuration

When used in the server context, user settings (from the UI/API) are applied after loading the configuration, taking precedence over environment variables and TOML settings but not over command-line arguments.

Here's an example of how to use `load_openhands_config()`:

```python
from openhands.core.config import load_openhands_config

# Load all configuration settings
config = load_openhands_config()

# Now you can access your configuration
llm_config = config.get_llm_config()
agent_config = config.get_agent_config()
sandbox_config = config.sandbox

# Use the configuration in your application
print(f"Using LLM model: {llm_config.model}")
print(f"Agent memory enabled: {agent_config.memory_enabled}")
print(f"Sandbox timeout: {sandbox_config.timeout}")
```

By using `load_openhands_config()`, you ensure that all configuration sources are properly loaded and processed, providing a consistent and fully initialized configuration for your application.

## Merging User Settings with Configuration

OpenHands provides a `ConfigurationMerger` utility for merging user settings with the application configuration:

```python
from openhands.core.config import ConfigurationMerger, OpenHandsConfig
from openhands.storage.data_models.settings import Settings

# Load the application configuration
config = OpenHandsConfig()

# Create or load user settings
settings = Settings(llm_model="gpt-4", max_iterations=100)

# Merge settings with configuration (settings take precedence)
merged_config = ConfigurationMerger.merge_settings_with_config(settings, config)

# You can also convert configuration to settings
settings = ConfigurationMerger.config_to_settings(config)
```

### Special Handling for MCP Configuration

MCP (Multi-Channel Provider) configuration is special because it represents a list of providers that can come from multiple sources. When merging MCP configuration:

1. Providers from `config.toml` appear first in the merged list
2. Providers from user settings are appended to the list

This allows both system-wide providers (from `config.toml`) and user-specific providers (from settings) to be used together.

## Additional Configuration Methods

While this document focuses on environment variable configuration, OpenHands also supports:

- Loading from TOML files
- Parsing command-line arguments

These methods are handled by separate functions in the config package.

## Conclusion

The OpenHands configuration system provides a flexible and type-safe way to manage application settings from multiple sources. By following the naming conventions and utilizing the provided functions, developers can easily customize the behavior of OpenHands components through environment variables, configuration files, and user settings.

The `ConfigurationMerger` utility provides a clean way to merge user settings with application configuration, ensuring that settings from different sources are properly combined according to the defined precedence rules.
