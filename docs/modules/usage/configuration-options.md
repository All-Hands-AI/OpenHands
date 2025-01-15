# Configuration Options

This guide details all configuration options available for OpenHands, helping you customize its behavior and integrate it with other services.

:::note
If you are running in [GUI Mode](https://docs.all-hands.dev/modules/usage/how-to/gui-mode), the settings available in the Settings UI will always
take precedence.
:::

## Core Configuration

The core configuration options are defined in the `[core]` section of the `config.toml` file.

### API Keys
- `e2b_api_key`
  - Type: `str`
  - Default: `""`
  - Description: API key for E2B

- `modal_api_token_id`
  - Type: `str`
  - Default: `""`
  - Description: API token ID for Modal

- `modal_api_token_secret`
  - Type: `str`
  - Default: `""`
  - Description: API token secret for Modal

### Workspace
- `workspace_base`
  - Type: `str`
  - Default: `"./workspace"`
  - Description: Base path for the workspace

- `cache_dir`
  - Type: `str`
  - Default: `"/tmp/cache"`
  - Description: Cache directory path

### Debugging and Logging
- `debug`
  - Type: `bool`
  - Default: `false`
  - Description: Enable debugging

- `disable_color`
  - Type: `bool`
  - Default: `false`
  - Description: Disable color in terminal output

### Trajectories
- `save_trajectory_path`
  - Type: `str`
  - Default: `"./trajectories"`
  - Description: Path to store trajectories (can be a folder or a file). If it's a folder, the trajectories will be saved in a file named with the session id name and .json extension, in that folder.

### File Store
- `file_store_path`
  - Type: `str`
  - Default: `"/tmp/file_store"`
  - Description: File store path

- `file_store`
  - Type: `str`
  - Default: `"memory"`
  - Description: File store type

- `file_uploads_allowed_extensions`
  - Type: `list of str`
  - Default: `[".*"]`
  - Description: List of allowed file extensions for uploads

- `file_uploads_max_file_size_mb`
  - Type: `int`
  - Default: `0`
  - Description: Maximum file size for uploads, in megabytes

- `file_uploads_restrict_file_types`
  - Type: `bool`
  - Default: `false`
  - Description: Restrict file types for file uploads

- `file_uploads_allowed_extensions`
  - Type: `list of str`
  - Default: `[".*"]`
  - Description: List of allowed file extensions for uploads

### Task Management
- `max_budget_per_task`
  - Type: `float`
  - Default: `0.0`
  - Description: Maximum budget per task (0.0 means no limit)

- `max_iterations`
  - Type: `int`
  - Default: `100`
  - Description: Maximum number of iterations

### Sandbox Configuration
- `workspace_mount_path_in_sandbox`
  - Type: `str`
  - Default: `"/workspace"`
  - Description: Path to mount the workspace in the sandbox

- `workspace_mount_path`
  - Type: `str`
  - Default: `""`
  - Description: Path to mount the workspace

- `workspace_mount_rewrite`
  - Type: `str`
  - Default: `""`
  - Description: Path to rewrite the workspace mount path to. You can usually ignore this, it refers to special cases of running inside another container.

### Miscellaneous
- `run_as_openhands`
  - Type: `bool`
  - Default: `true`
  - Description: Run as OpenHands

- `runtime`
  - Type: `str`
  - Default: `"eventstream"`
  - Description: Runtime environment

- `default_agent`
  - Type: `str`
  - Default: `"CodeActAgent"`
  - Description: Name of the default agent

- `jwt_secret`
  - Type: `str`
  - Default: `uuid.uuid4().hex`
  - Description: JWT secret for authentication. Please set it to your own value.

## LLM Configuration

The LLM (Large Language Model) configuration options are defined in the `[llm]` section of the `config.toml` file.

To use these with the docker command, pass in `-e LLM_<option>`. Example: `-e LLM_NUM_RETRIES`.

:::note
For development setups, you can also define custom named LLM configurations. See [Custom LLM Configurations](./llms/custom-llm-configs) for details.
:::

**AWS Credentials**
- `aws_access_key_id`
  - Type: `str`
  - Default: `""`
  - Description: AWS access key ID

- `aws_region_name`
  - Type: `str`
  - Default: `""`
  - Description: AWS region name

- `aws_secret_access_key`
  - Type: `str`
  - Default: `""`
  - Description: AWS secret access key

### API Configuration
- `api_key`
  - Type: `str`
  - Default: `None`
  - Description: API key to use

- `base_url`
  - Type: `str`
  - Default: `""`
  - Description: API base URL

- `api_version`
  - Type: `str`
  - Default: `""`
  - Description: API version

- `input_cost_per_token`
  - Type: `float`
  - Default: `0.0`
  - Description: Cost per input token

- `output_cost_per_token`
  - Type: `float`
  - Default: `0.0`
  - Description: Cost per output token

### Custom LLM Provider
- `custom_llm_provider`
  - Type: `str`
  - Default: `""`
  - Description: Custom LLM provider

### Embeddings
- `embedding_base_url`
  - Type: `str`
  - Default: `""`
  - Description: Embedding API base URL

- `embedding_deployment_name`
  - Type: `str`
  - Default: `""`
  - Description: Embedding deployment name

- `embedding_model`
  - Type: `str`
  - Default: `"local"`
  - Description: Embedding model to use

### Message Handling
- `max_message_chars`
  - Type: `int`
  - Default: `30000`
  - Description: The approximate maximum number of characters in the content of an event included in the prompt to the LLM. Larger observations are truncated.

- `max_input_tokens`
  - Type: `int`
  - Default: `0`
  - Description: Maximum number of input tokens

- `max_output_tokens`
  - Type: `int`
  - Default: `0`
  - Description: Maximum number of output tokens

### Model Selection
- `model`
  - Type: `str`
  - Default: `"claude-3-5-sonnet-20241022"`
  - Description: Model to use

### Retrying
- `num_retries`
  - Type: `int`
  - Default: `8`
  - Description: Number of retries to attempt

- `retry_max_wait`
  - Type: `int`
  - Default: `120`
  - Description: Maximum wait time (in seconds) between retry attempts

- `retry_min_wait`
  - Type: `int`
  - Default: `15`
  - Description: Minimum wait time (in seconds) between retry attempts

- `retry_multiplier`
  - Type: `float`
  - Default: `2.0`
  - Description: Multiplier for exponential backoff calculation

### Advanced Options
- `drop_params`
  - Type: `bool`
  - Default: `false`
  - Description: Drop any unmapped (unsupported) params without causing an exception

- `caching_prompt`
  - Type: `bool`
  - Default: `true`
  - Description: Using the prompt caching feature if provided by the LLM and supported

- `ollama_base_url`
  - Type: `str`
  - Default: `""`
  - Description: Base URL for the OLLAMA API

- `temperature`
  - Type: `float`
  - Default: `0.0`
  - Description: Temperature for the API

- `timeout`
  - Type: `int`
  - Default: `0`
  - Description: Timeout for the API

- `top_p`
  - Type: `float`
  - Default: `1.0`
  - Description: Top p for the API

- `disable_vision`
  - Type: `bool`
  - Default: `None`
  - Description: If model is vision capable, this option allows to disable image processing (useful for cost reduction)

## Agent Configuration

The agent configuration options are defined in the `[agent]` and `[agent.<agent_name>]` sections of the `config.toml` file.

### Microagent Configuration
- `micro_agent_name`
  - Type: `str`
  - Default: `""`
  - Description: Name of the micro agent to use for this agent

### Memory Configuration
- `memory_enabled`
  - Type: `bool`
  - Default: `false`
  - Description: Whether long-term memory (embeddings) is enabled

- `memory_max_threads`
  - Type: `int`
  - Default: `3`
  - Description: The maximum number of threads indexing at the same time for embeddings

### LLM Configuration
- `llm_config`
  - Type: `str`
  - Default: `'your-llm-config-group'`
  - Description: The name of the LLM config to use

### ActionSpace Configuration
- `function_calling`
  - Type: `bool`
  - Default: `true`
  - Description: Whether function calling is enabled

- `codeact_enable_browsing`
  - Type: `bool`
  - Default: `false`
  - Description: Whether browsing delegate is enabled in the action space (only works with function calling)

- `codeact_enable_llm_editor`
  - Type: `bool`
  - Default: `false`
  - Description: Whether LLM editor is enabled in the action space (only works with function calling)

- `codeact_enable_jupyter`
  - Type: `bool`
  - Default: `false`
  - Description: Whether Jupyter is enabled in the action space

### Microagent Usage
- `use_microagents`
  - Type: `bool`
  - Default: `true`
  - Description: Whether to use microagents at all

- `disabled_microagents`
  - Type: `list of str`
  - Default: `None`
  - Description: A list of microagents to disable

## Sandbox Configuration

The sandbox configuration options are defined in the `[sandbox]` section of the `config.toml` file.

To use these with the docker command, pass in `-e SANDBOX_<option>`. Example: `-e SANDBOX_TIMEOUT`.

### Execution
- `timeout`
  - Type: `int`
  - Default: `120`
  - Description: Sandbox timeout in seconds

- `user_id`
  - Type: `int`
  - Default: `1000`
  - Description: Sandbox user ID

### Container Image
- `base_container_image`
  - Type: `str`
  - Default: `"nikolaik/python-nodejs:python3.12-nodejs22"`
  - Description: Container image to use for the sandbox

### Networking
- `use_host_network`
  - Type: `bool`
  - Default: `false`
  - Description: Use host network

### Linting and Plugins
- `enable_auto_lint`
  - Type: `bool`
  - Default: `false`
  - Description: Enable auto linting after editing

- `initialize_plugins`
  - Type: `bool`
  - Default: `true`
  - Description: Whether to initialize plugins

### Dependencies and Environment
- `runtime_extra_deps`
  - Type: `str`
  - Default: `""`
  - Description: Extra dependencies to install in the runtime image

- `runtime_startup_env_vars`
  - Type: `dict`
  - Default: `{}`
  - Description: Environment variables to set at the launch of the runtime

### Evaluation
- `browsergym_eval_env`
  - Type: `str`
  - Default: `""`
  - Description: BrowserGym environment to use for evaluation

## Security Configuration

The security configuration options are defined in the `[security]` section of the `config.toml` file.

To use these with the docker command, pass in `-e SECURITY_<option>`. Example: `-e SECURITY_CONFIRMATION_MODE`.

### Confirmation Mode
- `confirmation_mode`
  - Type: `bool`
  - Default: `false`
  - Description: Enable confirmation mode

### Security Analyzer
- `security_analyzer`
  - Type: `str`
  - Default: `""`
  - Description: The security analyzer to use

---

> **Note**: Adjust configurations carefully, especially for memory, security, and network-related settings to ensure optimal performance and security.
Please note that the configuration options may be subject to change in future versions of OpenHands. It's recommended to refer to the official documentation for the most up-to-date information.
