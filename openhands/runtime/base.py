import atexit
import copy
import json
import os
import random
import string
from abc import abstractmethod
from pathlib import Path
from typing import Callable

from requests.exceptions import ConnectionError

from openhands.core.config import AppConfig, SandboxConfig
from openhands.core.exceptions import AgentRuntimeDisconnectedError
from openhands.core.logger import openhands_logger as logger
from openhands.events import EventSource, EventStream, EventStreamSubscriber
from openhands.events.action import (
    Action,
    ActionConfirmationStatus,
    BrowseInteractiveAction,
    BrowseURLAction,
    CmdRunAction,
    FileReadAction,
    FileWriteAction,
    IPythonRunCellAction,
)
from openhands.events.event import Event
from openhands.events.observation import (
    CmdOutputObservation,
    ErrorObservation,
    NullObservation,
    Observation,
    UserRejectObservation,
)
from openhands.events.serialization.action import ACTION_TYPE_TO_CLASS
from openhands.runtime.plugins import (
    JupyterRequirement,
    PluginRequirement,
    VSCodeRequirement,
)
from openhands.runtime.utils.edit import FileEditRuntimeMixin
from openhands.utils.async_utils import call_sync_from_async

STATUS_MESSAGES = {
    'STATUS$STARTING_RUNTIME': 'Starting runtime...',
    'STATUS$STARTING_CONTAINER': 'Starting container...',
    'STATUS$PREPARING_CONTAINER': 'Preparing container...',
    'STATUS$CONTAINER_STARTED': 'Container started.',
    'STATUS$WAITING_FOR_CLIENT': 'Waiting for client...',
}


def _default_env_vars(sandbox_config: SandboxConfig) -> dict[str, str]:
    ret = {}
    for key in os.environ:
        if key.startswith('SANDBOX_ENV_'):
            sandbox_key = key.removeprefix('SANDBOX_ENV_')
            ret[sandbox_key] = os.environ[key]
    if sandbox_config.enable_auto_lint:
        ret['ENABLE_AUTO_LINT'] = 'true'
    return ret


class Runtime(FileEditRuntimeMixin):
    """The runtime is how the agent interacts with the external environment.
    This includes a bash sandbox, a browser, and filesystem interactions.

    sid is the session id, which is used to identify the current user session.
    """

    sid: str
    config: AppConfig
    initial_env_vars: dict[str, str]
    attach_to_existing: bool
    status_callback: Callable | None

    def __init__(
        self,
        config: AppConfig,
        event_stream: EventStream,
        sid: str = 'default',
        plugins: list[PluginRequirement] | None = None,
        env_vars: dict[str, str] | None = None,
        status_callback: Callable | None = None,
        attach_to_existing: bool = False,
        headless_mode: bool = False,
    ):
        self.sid = sid
        self.event_stream = event_stream
        self.event_stream.subscribe(
            EventStreamSubscriber.RUNTIME, self.on_event, self.sid
        )
        self.plugins = (
            copy.deepcopy(plugins) if plugins is not None and len(plugins) > 0 else []
        )
        # add VSCode plugin if not in headless mode
        if not headless_mode:
            self.plugins.append(VSCodeRequirement())

        self.status_callback = status_callback
        self.attach_to_existing = attach_to_existing

        self.config = copy.deepcopy(config)
        atexit.register(self.close)

        self.initial_env_vars = _default_env_vars(config.sandbox)
        if env_vars is not None:
            self.initial_env_vars.update(env_vars)

        self._vscode_enabled = any(
            isinstance(plugin, VSCodeRequirement) for plugin in self.plugins
        )

        # Load mixins
        FileEditRuntimeMixin.__init__(self)

    def setup_initial_env(self) -> None:
        if self.attach_to_existing:
            return
        logger.debug(f'Adding env vars: {self.initial_env_vars}')
        self.add_env_vars(self.initial_env_vars)
        if self.config.sandbox.runtime_startup_env_vars:
            self.add_env_vars(self.config.sandbox.runtime_startup_env_vars)

    def close(self) -> None:
        pass

    def log(self, level: str, message: str) -> None:
        message = f'[runtime {self.sid}] {message}'
        getattr(logger, level)(message, stacklevel=2)

    def send_status_message(self, message_id: str):
        """Sends a status message if the callback function was provided."""
        if self.status_callback:
            msg = STATUS_MESSAGES.get(message_id, '')
            self.status_callback('info', message_id, msg)

    def send_error_message(self, message_id: str, message: str):
        if self.status_callback:
            self.status_callback('error', message_id, message)

    # ====================================================================

    def add_env_vars(self, env_vars: dict[str, str]) -> None:
        # Add env vars to the IPython shell (if Jupyter is used)
        if any(isinstance(plugin, JupyterRequirement) for plugin in self.plugins):
            code = 'import os\n'
            for key, value in env_vars.items():
                # Note: json.dumps gives us nice escaping for free
                code += f'os.environ["{key}"] = {json.dumps(value)}\n'
            code += '\n'
            obs = self.run_ipython(IPythonRunCellAction(code))
            self.log('debug', f'Added env vars to IPython: code={code}, obs={obs}')

        # Add env vars to the Bash shell
        cmd = ''
        for key, value in env_vars.items():
            # Note: json.dumps gives us nice escaping for free
            cmd += f'export {key}={json.dumps(value)}; '
        if not cmd:
            return
        cmd = cmd.strip()
        logger.debug(f'Adding env var: {cmd}')
        obs = self.run(CmdRunAction(cmd))
        if not isinstance(obs, CmdOutputObservation) or obs.exit_code != 0:
            raise RuntimeError(
                f'Failed to add env vars [{env_vars}] to environment: {obs.content}'
            )

    async def on_event(self, event: Event) -> None:
        if isinstance(event, Action):
            # set timeout to default if not set
            if event.timeout is None:
                event.timeout = self.config.sandbox.timeout
            assert event.timeout is not None
            try:
                observation: Observation = await call_sync_from_async(
                    self.run_action, event
                )
            except Exception as e:
                err_id = ''
                if isinstance(e, ConnectionError) or isinstance(
                    e, AgentRuntimeDisconnectedError
                ):
                    err_id = 'STATUS$ERROR_RUNTIME_DISCONNECTED'
                logger.error(
                    'Unexpected error while running action',
                    exc_info=True,
                    stack_info=True,
                )
                self.log('error', f'Problematic action: {str(event)}')
                self.send_error_message(err_id, str(e))
                self.close()
                return

            observation._cause = event.id  # type: ignore[attr-defined]
            observation.tool_call_metadata = event.tool_call_metadata

            # this might be unnecessary, since source should be set by the event stream when we're here
            source = event.source if event.source else EventSource.AGENT
            self.event_stream.add_event(observation, source)  # type: ignore[arg-type]

    def clone_repo(self, github_token: str | None, selected_repository: str | None):
        if not github_token or not selected_repository:
            return
        url = f'https://{github_token}@github.com/{selected_repository}.git'
        dir_name = selected_repository.split('/')[1]
        # add random branch name to avoid conflicts
        random_str = ''.join(
            random.choices(string.ascii_lowercase + string.digits, k=8)
        )
        branch_name = f'openhands-workspace-{random_str}'
        action = CmdRunAction(
            command=f'git clone {url} {dir_name} ; cd {dir_name} ; git checkout -b {branch_name}',
        )
        self.log('info', f'Cloning repo: {selected_repository}')
        self.run_action(action)

    def get_custom_microagents(self, selected_repository: str | None) -> list[str]:
        custom_microagents_content = []
        custom_microagents_dir = Path('.openhands') / 'microagents'

        dir_name = str(custom_microagents_dir)
        if selected_repository:
            dir_name = str(
                Path(selected_repository.split('/')[1]) / custom_microagents_dir
            )
        obs = self.read(FileReadAction(path='.openhands_instructions'))
        if isinstance(obs, ErrorObservation):
            self.log('debug', 'openhands_instructions not present')
        else:
            openhands_instructions = obs.content
            self.log('info', f'openhands_instructions: {openhands_instructions}')
            custom_microagents_content.append(openhands_instructions)

        files = self.list_files(dir_name)

        self.log('info', f'Found {len(files)} custom microagents.')

        for fname in files:
            content = self.read(
                FileReadAction(path=str(custom_microagents_dir / fname))
            ).content
            custom_microagents_content.append(content)

        return custom_microagents_content

    def run_action(self, action: Action) -> Observation:
        """Run an action and return the resulting observation.
        If the action is not runnable in any runtime, a NullObservation is returned.
        If the action is not supported by the current runtime, an ErrorObservation is returned.
        """
        if not action.runnable:
            return NullObservation('')
        if (
            hasattr(action, 'confirmation_state')
            and action.confirmation_state
            == ActionConfirmationStatus.AWAITING_CONFIRMATION
        ):
            return NullObservation('')
        action_type = action.action  # type: ignore[attr-defined]
        if action_type not in ACTION_TYPE_TO_CLASS:
            return ErrorObservation(f'Action {action_type} does not exist.')
        if not hasattr(self, action_type):
            return ErrorObservation(
                f'Action {action_type} is not supported in the current runtime.'
            )
        if (
            getattr(action, 'confirmation_state', None)
            == ActionConfirmationStatus.REJECTED
        ):
            return UserRejectObservation(
                'Action has been rejected by the user! Waiting for further user input.'
            )
        observation = getattr(self, action_type)(action)
        return observation

    # ====================================================================
    # Context manager
    # ====================================================================

    def __enter__(self) -> 'Runtime':
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()

    @abstractmethod
    async def connect(self) -> None:
        pass

    # ====================================================================
    # Action execution
    # ====================================================================

    @abstractmethod
    def run(self, action: CmdRunAction) -> Observation:
        pass

    @abstractmethod
    def run_ipython(self, action: IPythonRunCellAction) -> Observation:
        pass

    @abstractmethod
    def read(self, action: FileReadAction) -> Observation:
        pass

    @abstractmethod
    def write(self, action: FileWriteAction) -> Observation:
        pass

    @abstractmethod
    def browse(self, action: BrowseURLAction) -> Observation:
        pass

    @abstractmethod
    def browse_interactive(self, action: BrowseInteractiveAction) -> Observation:
        pass

    # ====================================================================
    # File operations
    # ====================================================================

    @abstractmethod
    def copy_to(self, host_src: str, sandbox_dest: str, recursive: bool = False):
        raise NotImplementedError('This method is not implemented in the base class.')

    @abstractmethod
    def list_files(self, path: str | None = None) -> list[str]:
        """List files in the sandbox.

        If path is None, list files in the sandbox's initial working directory (e.g., /workspace).
        """
        raise NotImplementedError('This method is not implemented in the base class.')

    @abstractmethod
    def copy_from(self, path: str) -> Path:
        """Zip all files in the sandbox and return a path in the local filesystem."""
        raise NotImplementedError('This method is not implemented in the base class.')

    # ====================================================================
    # VSCode
    # ====================================================================

    @property
    def vscode_enabled(self) -> bool:
        return self._vscode_enabled

    @property
    def vscode_url(self) -> str | None:
        raise NotImplementedError('This method is not implemented in the base class.')
