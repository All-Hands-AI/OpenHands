import os

from pydantic import BaseModel, Field


class SandboxConfig(BaseModel):
    """Configuration for the sandbox.

    Attributes:
        remote_runtime_api_url: The hostname for the Remote Runtime API.
        local_runtime_url: The default hostname for the local runtime. You may want to change to http://host.docker.internal for DIND environments
        base_container_image: The base container image from which to build the runtime image.
        runtime_container_image: The runtime container image to use.
        user_id: The user ID for the sandbox.
        timeout: The timeout for the default sandbox action execution.
        remote_runtime_init_timeout: The timeout for the remote runtime to start.
        remote_runtime_api_timeout: The timeout for the remote runtime API requests.
        enable_auto_lint: Whether to enable auto-lint.
        use_host_network: Whether to use the host network.
        initialize_plugins: Whether to initialize plugins.
        force_rebuild_runtime: Whether to force rebuild the runtime image.
        runtime_extra_deps: The extra dependencies to install in the runtime image (typically used for evaluation).
            This will be rendered into the end of the Dockerfile that builds the runtime image.
            It can contain any valid shell commands (e.g., pip install numpy).
            The path to the interpreter is available as $OH_INTERPRETER_PATH,
            which can be used to install dependencies for the OH-specific Python interpreter.
        runtime_startup_env_vars: The environment variables to set at the launch of the runtime.
            This is a dictionary of key-value pairs.
            This is useful for setting environment variables that are needed by the runtime.
            For example, for specifying the base url of website for browsergym evaluation.
        browsergym_eval_env: The BrowserGym environment to use for evaluation.
            Default is None for general purpose browsing. Check evaluation/miniwob and evaluation/webarena for examples.
        platform: The platform on which the image should be built. Default is None.
        remote_runtime_resource_factor: Factor to scale the resource allocation for remote runtime.
            Must be one of [1, 2, 4, 8]. Will only be used if the runtime is remote.
        enable_gpu: Whether to enable GPU.
        docker_runtime_kwargs: Additional keyword arguments to pass to the Docker runtime when running containers.
            This should be a JSON string that will be parsed into a dictionary.
    """

    remote_runtime_api_url: str | None = Field(default='http://localhost:8000')
    local_runtime_url: str = Field(default='http://localhost')
    keep_runtime_alive: bool = Field(default=False)
    rm_all_containers: bool = Field(default=False)
    api_key: str | None = Field(default=None)
    base_container_image: str = Field(
        default='nikolaik/python-nodejs:python3.12-nodejs22'
    )
    runtime_container_image: str | None = Field(default=None)
    user_id: int = Field(default=os.getuid() if hasattr(os, 'getuid') else 1000)
    timeout: int = Field(default=120)
    remote_runtime_init_timeout: int = Field(default=180)
    remote_runtime_api_timeout: int = Field(default=10)
    remote_runtime_enable_retries: bool = Field(default=False)
    remote_runtime_class: str | None = Field(
        default='sysbox'
    )  # can be "None" (default to gvisor) or "sysbox" (support docker inside runtime + more stable)
    enable_auto_lint: bool = Field(
        default=False  # once enabled, OpenHands would lint files after editing
    )
    use_host_network: bool = Field(default=False)
    runtime_extra_build_args: list[str] | None = Field(default=None)
    initialize_plugins: bool = Field(default=True)
    force_rebuild_runtime: bool = Field(default=False)
    runtime_extra_deps: str | None = Field(default=None)
    runtime_startup_env_vars: dict[str, str] = Field(default_factory=dict)
    browsergym_eval_env: str | None = Field(default=None)
    platform: str | None = Field(default=None)
    close_delay: int = Field(default=15)
    remote_runtime_resource_factor: int = Field(default=1)
    enable_gpu: bool = Field(default=False)
    docker_runtime_kwargs: str | None = Field(default=None)

    model_config = {'extra': 'forbid'}
