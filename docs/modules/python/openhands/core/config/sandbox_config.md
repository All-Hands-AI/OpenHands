# Sandbox Configuration

The `SandboxConfig` class defines the configuration options for the OpenHands sandbox environment.

## Configuration Options

### Remote Runtime Settings

- `remote_runtime_api_url` (str)
  - Default: `'http://localhost:8000'`
  - The hostname for the Remote Runtime API

- `local_runtime_url` (str)
  - Default: `'http://localhost'`
  - The default hostname for the local runtime
  - You may want to change to `http://host.docker.internal` for DIND environments

- `keep_runtime_alive` (bool)
  - Default: `True`
  - Whether to keep the runtime alive after execution

- `rm_all_containers` (bool)
  - Default: `False`
  - Whether to remove all containers after execution

### Container Settings

- `base_container_image` (str)
  - Default: `'nikolaik/python-nodejs:python3.12-nodejs22'`
  - The base container image from which to build the runtime image

- `runtime_container_image` (str | None)
  - Default: `None`
  - The runtime container image to use

- `user_id` (int)
  - Default: System's UID or 1000
  - The user ID for the sandbox

### Execution Settings

- `timeout` (int)
  - Default: `120`
  - The timeout for the default sandbox action execution (in seconds)

- `remote_runtime_init_timeout` (int)
  - Default: `180`
  - The timeout for the remote runtime to start (in seconds)

- `close_delay` (int)
  - Default: `900`
  - Delay before closing the runtime (in seconds)

### Runtime Configuration

- `enable_auto_lint` (bool)
  - Default: `False`
  - Whether to enable auto-lint after editing files

- `use_host_network` (bool)
  - Default: `False`
  - Whether to use the host network

- `initialize_plugins` (bool)
  - Default: `True`
  - Whether to initialize plugins

- `force_rebuild_runtime` (bool)
  - Default: `False`
  - Whether to force rebuild the runtime image

### Dependencies and Environment

- `runtime_extra_deps` (str | None)
  - Default: `None`
  - Extra dependencies to install in the runtime image (typically used for evaluation)
  - Will be rendered into the end of the Dockerfile that builds the runtime image
  - Can contain any valid shell commands (e.g., `pip install numpy`)
  - The path to the interpreter is available as `$OH_INTERPRETER_PATH`

- `runtime_startup_env_vars` (dict[str, str])
  - Default: `{}`
  - Environment variables to set at runtime launch
  - Useful for setting environment variables needed by the runtime
  - Example: specifying base URL for browsergym evaluation

### Resource Management

- `remote_runtime_resource_factor` (int)
  - Default: `1`
  - Factor to scale resource allocation for remote runtime
  - Must be one of [1, 2, 4, 8]
  - Only used if the runtime is remote

- `enable_gpu` (bool)
  - Default: `False`
  - Whether to enable GPU support

### Docker Runtime Configuration

- `docker_runtime_kwargs` (str | None)
  - Default: `None`
  - Additional keyword arguments to pass to the Docker runtime
  - Should be a JSON string that will be parsed into a dictionary
  - Example in config.toml:
    ```toml
    docker_runtime_kwargs = '{"mem_limit": "4g", "cpu_quota": 100000}'
    ```

### Evaluation

- `browsergym_eval_env` (str | None)
  - Default: `None`
  - The BrowserGym environment to use for evaluation
  - Default is None for general purpose browsing
  - Check evaluation/miniwob and evaluation/webarena for examples

### Build Configuration

- `platform` (str | None)
  - Default: `None`
  - The platform on which the image should be built

- `runtime_extra_build_args` (list[str] | None)
  - Default: `None`
  - Additional build arguments for the runtime