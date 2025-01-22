# Custom LLM Configurations

OpenHands supports defining multiple named LLM configurations in your `config.toml` file. This feature allows you to use different LLM configurations for different purposes, such as using a cheaper model for tasks that don't require high-quality responses, or using different models with different parameters for specific agents.

## How It Works

Named LLM configurations are defined in the `config.toml` file using sections that start with `llm.`. For example:

```toml
# Default LLM configuration
[llm]
model = "gpt-4"
api_key = "your-api-key"
temperature = 0.0

# Custom LLM configuration for a cheaper model
[llm.gpt3]
model = "gpt-3.5-turbo"
api_key = "your-api-key"
temperature = 0.2

# Another custom configuration with different parameters
[llm.high-creativity]
model = "gpt-4"
api_key = "your-api-key"
temperature = 0.8
top_p = 0.9
```

Each named configuration inherits all settings from the default `[llm]` section and can override any of those settings. You can define as many custom configurations as needed.

## Using Custom Configurations

### With Agents

You can specify which LLM configuration an agent should use by setting the `llm_config` parameter in the agent's configuration section:

```toml
[agent.RepoExplorerAgent]
# Use the cheaper GPT-3 configuration for this agent
llm_config = 'gpt3'

[agent.CodeWriterAgent]
# Use the high creativity configuration for this agent
llm_config = 'high-creativity'
```

### Configuration Options

Each named LLM configuration supports all the same options as the default LLM configuration. These include:

- Model selection (`model`)
- API configuration (`api_key`, `base_url`, etc.)
- Model parameters (`temperature`, `top_p`, etc.)
- Retry settings (`num_retries`, `retry_multiplier`, etc.)
- Token limits (`max_input_tokens`, `max_output_tokens`)
- And all other LLM configuration options

For a complete list of available options, see the LLM Configuration section in the [Configuration Options](../configuration-options) documentation.

## Use Cases

Custom LLM configurations are particularly useful in several scenarios:

- **Cost Optimization**: Use cheaper models for tasks that don't require high-quality responses, like repository exploration or simple file operations.
- **Task-Specific Tuning**: Configure different temperature and top_p values for tasks that require different levels of creativity or determinism.
- **Different Providers**: Use different LLM providers or API endpoints for different tasks.
- **Testing and Development**: Easily switch between different model configurations during development and testing.

## Example: Cost Optimization

A practical example of using custom LLM configurations to optimize costs:

```toml
# Default configuration using GPT-4 for high-quality responses
[llm]
model = "gpt-4"
api_key = "your-api-key"
temperature = 0.0

# Cheaper configuration for repository exploration
[llm.repo-explorer]
model = "gpt-3.5-turbo"
temperature = 0.2

# Configuration for code generation
[llm.code-gen]
model = "gpt-4"
temperature = 0.0
max_output_tokens = 2000

[agent.RepoExplorerAgent]
llm_config = 'repo-explorer'

[agent.CodeWriterAgent]
llm_config = 'code-gen'
```

In this example:
- Repository exploration uses a cheaper model since it mainly involves understanding and navigating code
- Code generation uses GPT-4 with a higher token limit for generating larger code blocks
- The default configuration remains available for other tasks

# Custom Configurations with Reserved Names

OpenHands can use custom LLM configurations named with reserved names, for specific use cases. If you specify the model and other settings under the reserved names, then OpenHands will load and them for a specific purpose. As of now, one such configuration is implemented: draft editor.

## Draft Editor Configuration

The `draft_editor` configuration is a group of settings you can provide, to specify the model to use for preliminary drafting of code edits, for any tasks that involve editing and refining code. You need to provide it under the section `[llm.draft_editor]`.

For example, you can define in `config.toml` a draft editor like this:

```toml
[llm.draft_editor]
model = "gpt-4"
temperature = 0.2
top_p = 0.95
presence_penalty = 0.0
frequency_penalty = 0.0
```

This configuration:
- Uses GPT-4 for high-quality edits and suggestions
- Sets a low temperature (0.2) to maintain consistency while allowing some flexibility
- Uses a high top_p value (0.95) to consider a wide range of token options
- Disables presence and frequency penalties to maintain focus on the specific edits needed

Use this configuration when you want to let an LLM draft edits before making them. In general, it may be useful to:
- Review and suggest code improvements
- Refine existing content while maintaining its core meaning
- Make precise, focused changes to code or text

:::note
Custom LLM configurations are only available when using OpenHands in development mode, via `main.py` or `cli.py`. When running via `docker run`, please use the standard configuration options.
:::
