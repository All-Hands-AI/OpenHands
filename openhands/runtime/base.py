import asyncio
import atexit
import copy
import json
import os
import shutil
import tempfile
from abc import abstractmethod
from pathlib import Path
from types import MappingProxyType
from typing import Callable, cast
from zipfile import ZipFile

import httpx

from openhands.core.config import AppConfig, SandboxConfig
from openhands.core.exceptions import AgentRuntimeDisconnectedError
from openhands.core.logger import openhands_logger as logger
from openhands.events import EventSource, EventStream, EventStreamSubscriber
from openhands.events.action import (
    Action,
    CmdRunAction,
    FileReadAction,
    FileWriteAction,
    IPythonRunCellAction,
)
from openhands.events.action.mcp import MCPAction
from openhands.events.event import Event
from openhands.events.observation import (
    CmdOutputObservation,
    ErrorObservation,
    NullObservation,
    Observation,
)
from openhands.integrations.provider import (
    PROVIDER_TOKEN_TYPE,
    ProviderHandler,
)
from openhands.microagent import (
    BaseMicroagent,
    load_microagents_from_dir,
)
from openhands.runtime.plugins import (
    JupyterRequirement,
    PluginRequirement,
    VSCodeRequirement,
)
from openhands.runtime.utils.edit import FileEditRuntimeMixin
from openhands.runtime.utils.git_handler import CommandResult, GitHandler
from openhands.utils.async_utils import (
    GENERAL_TIMEOUT,
    call_async_from_sync,
    call_sync_from_async,
)

STATUS_MESSAGES = {
    'STATUS$STARTING_RUNTIME': 'Starting runtime...',
    'STATUS$STARTING_CONTAINER': 'Starting container...',
    'STATUS$PREPARING_CONTAINER': 'Preparing container...',
    'STATUS$CONTAINER_STARTED': 'Container started.',
    'STATUS$WAITING_FOR_CLIENT': 'Waiting for client...',
    'STATUS$SETTING_UP_WORKSPACE': 'Setting up workspace...',
    'STATUS$SETTING_UP_GIT_HOOKS': 'Setting up git hooks...',
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

    @abstractmethod
    def run(self, action: Action) -> Observation:
        """Run an action and return the observation."""
        pass

    @abstractmethod
    def run_action(self, action: Action) -> Observation:
        """Run an action and return the observation."""
        pass

    @abstractmethod
    async def call_tool_mcp(self, action: MCPAction) -> Observation:
        """Call an MCP tool and return the observation."""
        pass

    @abstractmethod
    def list_files(self, path: str) -> list[str]:
        """List files in a directory."""
        pass

    @abstractmethod
    def copy_from(self, path: str) -> Path:
        """Copy a file from the sandbox to the host."""
        pass

    @abstractmethod
    def copy_to(self, src: str, dst: str, recursive: bool = False) -> None:
        """Copy a file from the host to the sandbox."""
        pass

    @abstractmethod
    def _execute_shell_fn_git_handler(
        self, cmd: str, cwd: str | None = None
    ) -> CommandResult:
        """Execute a shell command for git handler."""
        pass

    @abstractmethod
    def read(self, action: FileReadAction) -> Observation:
        """Read a file and return the observation."""
        pass

    @abstractmethod
    def write(self, action: FileWriteAction) -> Observation:
        """Write a file and return the observation."""
        pass

    @abstractmethod
    def run_ipython(self, action: IPythonRunCellAction) -> Observation:
        """Run an IPython cell and return the observation."""
        pass

    def _load_microagents_from_dir(self, directory_path: Path) -> list[BaseMicroagent]:
        """Helper method to load microagents from a directory."""
        loaded_agents: list[BaseMicroagent] = []

        # Check if directory exists
        try:
            files = self.list_files(str(directory_path))
            if not files:
                return loaded_agents

            self.log('info', f'Found {len(files)} files in {directory_path}.')

            # Copy files from sandbox to local filesystem
            zip_path = self.copy_from(str(directory_path))
            microagent_folder = tempfile.mkdtemp()

            try:
                # Extract files
                with ZipFile(zip_path, 'r') as zip_file:
                    zip_file.extractall(microagent_folder)

                # Add debug print of directory structure
                self.log('debug', f'Microagent folder structure for {directory_path}:')
                for root, _, files in os.walk(microagent_folder):
                    relative_path = os.path.relpath(root, microagent_folder)
                    self.log('debug', f'Directory: {relative_path}/')
                    for file in files:
                        self.log(
                            'debug', f'  File: {os.path.join(relative_path, file)}'
                        )

                # Load microagents
                repo_agents, knowledge_agents = load_microagents_from_dir(
                    microagent_folder
                )
                loaded_agents.extend(repo_agents.values())
                loaded_agents.extend(knowledge_agents.values())

                self.log(
                    'info',
                    f'Loaded {len(repo_agents)} repo agents and {len(knowledge_agents)} knowledge agents from {directory_path}',
                )
            finally:
                # Clean up
                if os.path.exists(zip_path):
                    zip_path.unlink()
                shutil.rmtree(microagent_folder)
        except Exception as e:
            self.log('debug', f'Error loading microagents from {directory_path}: {e}')

        return loaded_agents

    sid: str
    config: AppConfig
    initial_env_vars: dict[str, str]
    attach_to_existing: bool
    status_callback: Callable[[str, str, str], None] | None

    def __init__(
        self,
        config: AppConfig,
        event_stream: EventStream,
        sid: str = 'default',
        plugins: list[PluginRequirement] | None = None,
        env_vars: dict[str, str] | None = None,
        status_callback: Callable[[str, str, str], None] | None = None,
        attach_to_existing: bool = False,
        headless_mode: bool = False,
        user_id: str | None = None,
        git_provider_tokens: PROVIDER_TOKEN_TYPE | None = None,
    ):
        self.git_handler = GitHandler(
            execute_shell_fn=self._execute_shell_fn_git_handler
        )
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

        self.provider_handler = ProviderHandler(
            provider_tokens=git_provider_tokens
            or cast(PROVIDER_TOKEN_TYPE, MappingProxyType({})),
            external_auth_id=user_id,
            external_token_manager=True,
        )
        raw_env_vars: dict[str, str] = call_async_from_sync(
            self.provider_handler.get_env_vars, GENERAL_TIMEOUT, True, None, False
        )
        self.initial_env_vars.update(raw_env_vars)

        self._vscode_enabled = any(
            isinstance(plugin, VSCodeRequirement) for plugin in self.plugins
        )

        # Load mixins
        FileEditRuntimeMixin.__init__(
            self, enable_llm_editor=config.get_agent_config().enable_llm_editor
        )

        self.user_id = user_id
        self.git_provider_tokens = git_provider_tokens

    def setup_initial_env(self) -> None:
        if self.attach_to_existing:
            return
        logger.debug(f'Adding env vars: {self.initial_env_vars.keys()}')
        self.add_env_vars(self.initial_env_vars)
        if self.config.sandbox.runtime_startup_env_vars:
            self.add_env_vars(self.config.sandbox.runtime_startup_env_vars)

    def close(self) -> None:
        """
        This should only be called by conversation manager or closing the session.
        If called for instance by error handling, it could prevent recovery.
        """
        pass

    @classmethod
    async def delete(cls, conversation_id: str) -> None:
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
        env_vars = {key.upper(): value for key, value in env_vars.items()}

        # Add env vars to the IPython shell (if Jupyter is used)
        if any(isinstance(plugin, JupyterRequirement) for plugin in self.plugins):
            code = 'import os\n'
            for key, value in env_vars.items():
                # Note: json.dumps gives us nice escaping for free
                code += f'os.environ["{key}"] = {json.dumps(value)}\n'
            code += '\n'
            self.run_ipython(IPythonRunCellAction(code))
            # Note: we don't log the vars values, they're leaking info
            logger.debug('Added env vars to IPython')

        # Add env vars to the Bash shell and .bashrc for persistence
        cmd = ''
        bashrc_cmd = ''
        for key, value in env_vars.items():
            # Note: json.dumps gives us nice escaping for free
            cmd += f'export {key}={json.dumps(value)}; '
            # Add to .bashrc if not already present
            bashrc_cmd += f'grep -q "^export {key}=" ~/.bashrc || echo "export {key}={json.dumps(value)}" >> ~/.bashrc; '
        if not cmd:
            return
        cmd = cmd.strip()
        logger.debug(
            'Adding env vars to bash'
        )  # don't log the vars values, they're leaking info

        obs = self.run(CmdRunAction(cmd))
        if not isinstance(obs, CmdOutputObservation) or obs.exit_code != 0:
            raise RuntimeError(
                f'Failed to add env vars [{env_vars.keys()}] to environment: {obs.content}'
            )

        # Add to .bashrc for persistence
        bashrc_cmd = bashrc_cmd.strip()
        logger.debug(f'Adding env var to .bashrc: {env_vars.keys()}')
        obs = self.run(CmdRunAction(bashrc_cmd))
        if not isinstance(obs, CmdOutputObservation) or obs.exit_code != 0:
            raise RuntimeError(
                f'Failed to add env vars [{env_vars.keys()}] to .bashrc: {obs.content}'
            )

    def on_event(self, event: Event) -> None:
        if isinstance(event, Action):
            asyncio.get_event_loop().run_until_complete(self._handle_action(event))

    async def _export_latest_git_provider_tokens(self, event: Action) -> None:
        """
        Refresh runtime provider tokens when agent attemps to run action with provider token
        """
        if not self.user_id:
            return

        providers_called = ProviderHandler.check_cmd_action_for_provider_token_ref(
            event
        )

        if not providers_called:
            return

        logger.info(f'Fetching latest provider tokens for runtime: {self.sid}')
        env_vars = await self.provider_handler.get_env_vars(
            providers=providers_called, expose_secrets=False, get_latest=True
        )

        if len(env_vars) == 0:
            return

        try:
            await self.provider_handler.set_event_stream_secrets(
                self.event_stream, env_vars=env_vars
            )
            self.add_env_vars(self.provider_handler.expose_env_vars(env_vars))
        except Exception as e:
            logger.warning(
                f'Failed export latest github token to runtime: {self.sid}, {e}'
            )

    async def _handle_action(self, event: Action) -> None:
        if event.timeout is None:
            # We don't block the command if this is a default timeout action
            event.set_hard_timeout(self.config.sandbox.timeout, blocking=False)
        assert event.timeout is not None
        try:
            await self._export_latest_git_provider_tokens(event)
            if isinstance(event, MCPAction):
                observation: Observation = await self.call_tool_mcp(event)
            else:
                observation = await call_sync_from_async(self.run_action, event)
        except Exception as e:
            err_id = ''
            if isinstance(e, httpx.NetworkError) or isinstance(
                e, AgentRuntimeDisconnectedError
            ):
                err_id = 'STATUS$ERROR_RUNTIME_DISCONNECTED'
            error_message = f'{type(e).__name__}: {str(e)}'
            self.log('error', f'Unexpected error while running action: {error_message}')
            self.log('error', f'Problematic action: {str(event)}')
            self.send_error_message(err_id, error_message)
            return

        observation._cause = event.id  # type: ignore[attr-defined]
        observation.tool_call_metadata = event.tool_call_metadata

        # this might be unnecessary, since source should be set by the event stream when we're here
        source = event.source if event.source else EventSource.AGENT
        if isinstance(observation, NullObservation):
            # don't add null observations to the event stream
            return
        self.event_stream.add_event(observation, source)  # type: ignore[arg-type]

    def maybe_setup_git_hooks(self):
        """Set up git hooks if .openhands/pre-commit.sh exists in the workspace or repository."""
        pre_commit_script = '.openhands/pre-commit.sh'
        read_obs = self.read(FileReadAction(path=pre_commit_script))
        if isinstance(read_obs, ErrorObservation):
            return

        if self.status_callback:
            self.status_callback(
                'info', 'STATUS$SETTING_UP_GIT_HOOKS', 'Setting up git hooks...'
            )

        # Ensure the git hooks directory exists
        action = CmdRunAction('mkdir -p .git/hooks')
        obs = self.run_action(action)
        if isinstance(obs, CmdOutputObservation) and obs.exit_code != 0:
            self.log('error', f'Failed to create git hooks directory: {obs.content}')
            return

        # Make the pre-commit script executable
        action = CmdRunAction(f'chmod +x {pre_commit_script}')
        obs = self.run_action(action)
        if isinstance(obs, CmdOutputObservation) and obs.exit_code != 0:
            self.log(
                'error', f'Failed to make pre-commit script executable: {obs.content}'
            )
            return

        # Check if there's an existing pre-commit hook
        pre_commit_hook = '.git/hooks/pre-commit'
        pre_commit_local = '.git/hooks/pre-commit.local'

        # Read the existing pre-commit hook if it exists
        read_obs = self.read(FileReadAction(path=pre_commit_hook))
        if not isinstance(read_obs, ErrorObservation):
            # If the existing hook wasn't created by OpenHands, preserve it
            if 'This hook was installed by OpenHands' not in read_obs.content:
                self.log('info', 'Preserving existing pre-commit hook')
                # Move the existing hook to pre-commit.local
                action = CmdRunAction(f'mv {pre_commit_hook} {pre_commit_local}')
                obs = self.run_action(action)
                if isinstance(obs, CmdOutputObservation) and obs.exit_code != 0:
                    self.log(
                        'error',
                        f'Failed to preserve existing pre-commit hook: {obs.content}',
                    )
                    return

                # Make it executable
                action = CmdRunAction(f'chmod +x {pre_commit_local}')
                obs = self.run_action(action)
                if isinstance(obs, CmdOutputObservation) and obs.exit_code != 0:
                    self.log(
                        'error',
                        f'Failed to make preserved hook executable: {obs.content}',
                    )
                    return

        # Create the pre-commit hook that calls our script
        pre_commit_hook_content = f"""#!/bin/bash
# This hook was installed by OpenHands
# It calls the pre-commit script in the .openhands directory

if [ -x "{pre_commit_script}" ]; then
    source "{pre_commit_script}"
    exit $?
else
    echo "Warning: {pre_commit_script} not found or not executable"
    exit 0
fi
"""

        # Write the pre-commit hook
        write_obs = self.write(
            FileWriteAction(path=pre_commit_hook, content=pre_commit_hook_content)
        )
        if isinstance(write_obs, ErrorObservation):
            self.log('error', f'Failed to write pre-commit hook: {write_obs.content}')
            return

        # Make the pre-commit hook executable
        action = CmdRunAction(f'chmod +x {pre_commit_hook}')
        obs = self.run_action(action)
        if isinstance(obs, CmdOutputObservation) and obs.exit_code != 0:
            self.log(
                'error', f'Failed to make pre-commit hook executable: {obs.content}'
            )
            return

        self.log('info', 'Git pre-commit hook installed successfully')

    def get_microagents_from_selected_repo(
        self, selected_repository: str | None
    ) -> list[BaseMicroagent]:
        """Load microagents from all sources:
        1. Custom microagents directory (~/.openhands/microagents/)
        2. User's .openhands repository
        3. Organization's .openhands repository
        4. Selected repository's .openhands/microagents directory

        This is the main entry point for loading microagents.
        """
        loaded_microagents: list[BaseMicroagent] = []
        workspace_root = Path(self.config.workspace_mount_path_in_sandbox)
        selected_repo_root = (
            workspace_root / selected_repository.split('/')[-1]
            if selected_repository
            else None
        )

        # 1. Load from custom microagents directory
        custom_microagents_path = os.path.expanduser(self.config.custom_microagents_dir)
        if os.path.exists(custom_microagents_path):
            # Copy the custom microagents directory to the sandbox
            sandbox_custom_dir = workspace_root / '.custom_microagents'
            try:
                # Create the directory if it doesn't exist
                self.run_action(CmdRunAction(f'mkdir -p {sandbox_custom_dir}'))

                # Copy files from host to sandbox
                self.copy_to(
                    custom_microagents_path, str(sandbox_custom_dir), recursive=True
                )

                # Load microagents from the copied directory
                self.log(
                    'info', f'Loading custom microagents from {sandbox_custom_dir}'
                )
                custom_microagents = self._load_microagents_from_dir(sandbox_custom_dir)
                loaded_microagents.extend(custom_microagents)
            except Exception as e:
                self.log('warning', f'Failed to load custom microagents: {e}')

        # 2. Load from user's .openhands repository if it exists
        # We need to check all user directories in the workspace root
        try:
            # List all directories in workspace root
            workspace_files = self.list_files(str(workspace_root))
            for user_dir in workspace_files:
                # Skip if not a directory
                if not user_dir.endswith('/'):
                    continue
                user_dir = user_dir.rstrip('/')
                user_dir_path = Path(user_dir)

                # Check if .openhands directory exists
                check_cmd = f'[ -d "{user_dir_path / ".openhands"}" ] && echo "exists" || echo "not exists"'
                check_obs = self.run_action(CmdRunAction(check_cmd))
                if (
                    not isinstance(check_obs, CmdOutputObservation)
                    or 'exists' not in check_obs.content
                ):
                    continue

                # Load microagents from user's .openhands/microagents directory
                user_microagents_dir = user_dir_path / '.openhands' / 'microagents'
                self.log(
                    'info',
                    f'Loading repository microagents from {user_microagents_dir}',
                )
                try:
                    repo_microagents = self._load_microagents_from_dir(
                        user_microagents_dir
                    )
                    loaded_microagents.extend(repo_microagents)
                except Exception as e:
                    self.log('debug', f'Error loading microagents from {user_dir}: {e}')
        except Exception as e:
            self.log('debug', f'Error loading microagents from user directories: {e}')

        # 3. Load from selected repository's .openhands/microagents directory
        if selected_repo_root is not None:
            try:
                repo_microagents_dir = selected_repo_root / '.openhands' / 'microagents'
                self.log(
                    'info',
                    f'Loading repository microagents from {repo_microagents_dir}',
                )
                try:
                    repo_microagents = self._load_microagents_from_dir(
                        repo_microagents_dir
                    )
                    loaded_microagents.extend(repo_microagents)
                except Exception as e:
                    self.log(
                        'debug', f'Error loading microagents from selected repo: {e}'
                    )
            except Exception as e:
                self.log('debug', f'Error loading microagents from selected repo: {e}')

        return loaded_microagents
