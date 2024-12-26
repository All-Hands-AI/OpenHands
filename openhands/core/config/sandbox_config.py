import os
from dataclasses import dataclass, field, fields

from openhands.core.config.config_utils import get_field_info


@dataclass
class SandboxConfig:
    """Configuration for the sandbox.

    Attributes:
        remote_runtime_api_url: The hostname for the Remote Runtime API.
        local_runtime_url: The default hostname for the local runtime. You may want to change to http://host.docker.internal for DIND environments
        base_container_image: The base container image from which to build the runtime image.
        runtime_container_image: The runtime container image to use.
        user_id: The user ID for the sandbox.
        timeout: The timeout for the default sandbox action execution.
        remote_runtime_init_timeout: The timeout for the remote runtime to start.
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
    """

    remote_runtime_api_url: str = 'http://localhost:8000'
    local_runtime_url: str = 'http://localhost'
    keep_runtime_alive: bool = True
    rm_all_containers: bool = False
    api_key: str | None = None
    base_container_image: str = 'nikolaik/python-nodejs:python3.12-nodejs22'  # default to nikolaik/python-nodejs:python3.12-nodejs22 for eventstream runtime
    runtime_container_image: str | None = None
    user_id: int = os.getuid() if hasattr(os, 'getuid') else 1000
    timeout: int = 120
    remote_runtime_init_timeout: int = 180
    enable_auto_lint: bool = (
        False  # once enabled, OpenHands would lint files after editing
    )
    use_host_network: bool = False
    runtime_extra_build_args: list[str] | None = None
    initialize_plugins: bool = True
    force_rebuild_runtime: bool = False
    runtime_extra_deps: str | None = None
    runtime_startup_env_vars: dict[str, str] = field(default_factory=dict)
    browsergym_eval_env: str | None = None
    platform: str | None = None
    close_delay: int = 15
    remote_runtime_resource_factor: int = 1

    def defaults_to_dict(self) -> dict:
        """Serialize fields to a dict for the frontend, including type hints, defaults, and whether it's optional."""
        dict = {}
        for f in fields(self):
            dict[f.name] = get_field_info(f)
        return dict

    def __str__(self):
        attr_str = []
        for f in fields(self):
            attr_name = f.name
            attr_value = getattr(self, f.name)

            attr_str.append(f'{attr_name}={repr(attr_value)}')

        return f"SandboxConfig({', '.join(attr_str)})"

    def __repr__(self):
        return self.__str__()
