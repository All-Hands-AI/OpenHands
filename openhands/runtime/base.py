import asyncio
import atexit
import copy
import json
import os
import random
import shutil
import string
import tempfile
from abc import abstractmethod
from pathlib import Path
from types import MappingProxyType
from typing import Callable, cast
from zipfile import ZipFile

import httpx

from openhands.core.config import OpenHandsConfig, SandboxConfig
from openhands.core.config.mcp_config import MCPConfig, MCPStdioServerConfig
from openhands.core.exceptions import AgentRuntimeDisconnectedError
from openhands.core.logger import openhands_logger as logger
from openhands.events import EventSource, EventStream, EventStreamSubscriber
from openhands.events.action import (
    Action,
    ActionConfirmationStatus,
    AgentThinkAction,
    BrowseInteractiveAction,
    BrowseURLAction,
    CmdRunAction,
    FileEditAction,
    FileReadAction,
    FileWriteAction,
    IPythonRunCellAction,
)
from openhands.events.action.mcp import MCPAction
from openhands.events.event import Event
from openhands.events.observation import (
    AgentThinkObservation,
    CmdOutputObservation,
    ErrorObservation,
    FileReadObservation,
    NullObservation,
    Observation,
    UserRejectObservation,
)
from openhands.events.serialization.action import ACTION_TYPE_TO_CLASS
from openhands.integrations.provider import (
    PROVIDER_TOKEN_TYPE,
    ProviderHandler,
    ProviderType,
)
from openhands.integrations.service_types import AuthenticationError
from openhands.microagent import (
    BaseMicroagent,
    load_microagents_from_dir,
)
from openhands.runtime.plugins import (
    JupyterRequirement,
    PluginRequirement,
    VSCodeRequirement,
)
from openhands.runtime.runtime_status import RuntimeStatus
from openhands.runtime.utils.edit import FileEditRuntimeMixin
from openhands.runtime.utils.git_handler import CommandResult, GitHandler
from openhands.utils.async_utils import (
    GENERAL_TIMEOUT,
    call_async_from_sync,
    call_sync_from_async,
)


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
    """Abstract base class for agent runtime environments.

    This is an extension point in OpenHands that allows applications to customize how
    agents interact with the external environment. The runtime provides a sandbox with:
    - Bash shell access
    - Browser interaction
    - Filesystem operations
    - Git operations
    - Environment variable management

    Applications can substitute their own implementation by:
    1. Creating a class that inherits from Runtime
    2. Implementing all required methods
    3. Setting the runtime name in configuration or using get_runtime_cls()

    The class is instantiated via get_impl() in get_runtime_cls().

    Built-in implementations include:
    - DockerRuntime: Containerized environment using Docker
    - E2BRuntime: Secure sandbox using E2B
    - RemoteRuntime: Remote execution environment
    - ModalRuntime: Scalable cloud environment using Modal
    - LocalRuntime: Local execution for development
    - DaytonaRuntime: Cloud development environment using Daytona

    Args:
        sid: Session ID that uniquely identifies the current user session
    """

    sid: str
    config: OpenHandsConfig
    initial_env_vars: dict[str, str]
    attach_to_existing: bool
    status_callback: Callable[[str, str, str], None] | None
    runtime_status: RuntimeStatus | None
    _runtime_initialized: bool = False

    def __init__(
        self,
        config: OpenHandsConfig,
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
        if event_stream:
            event_stream.subscribe(
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
        self.runtime_status = None

    @property
    def runtime_initialized(self) -> bool:
        return self._runtime_initialized

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

    def set_runtime_status(self, runtime_status: RuntimeStatus):
        """Sends a status message if the callback function was provided."""
        self.runtime_status = runtime_status
        if self.status_callback:
            msg_id: str = runtime_status.value  # type: ignore
            self.status_callback('info', msg_id, runtime_status.message)

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

        # Check if we're on Windows
        import os
        import sys

        is_windows = os.name == 'nt' or sys.platform == 'win32'

        if is_windows:
            # Add env vars using PowerShell commands for Windows
            cmd = ''
            for key, value in env_vars.items():
                # Use PowerShell's $env: syntax for environment variables
                # Note: json.dumps gives us nice escaping for free
                cmd += f'$env:{key} = {json.dumps(value)}; '

            if not cmd:
                return

            cmd = cmd.strip()
            logger.debug('Adding env vars to PowerShell')  # don't log the values

            obs = self.run(CmdRunAction(cmd))
            if not isinstance(obs, CmdOutputObservation) or obs.exit_code != 0:
                raise RuntimeError(
                    f'Failed to add env vars [{env_vars.keys()}] to environment: {obs.content}'
                )

            # We don't add to profile persistence on Windows as it's more complex
            # and varies between PowerShell versions
            logger.debug(f'Added env vars to PowerShell session: {env_vars.keys()}')

        else:
            # Original bash implementation for Unix systems
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
            logger.debug('Adding env vars to bash')  # don't log the values

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
            if self.event_stream:
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

    async def clone_or_init_repo(
        self,
        git_provider_tokens: PROVIDER_TOKEN_TYPE | None,
        selected_repository: str | None,
        selected_branch: str | None,
    ) -> str:
        if not selected_repository:
            # In SaaS mode (indicated by user_id being set), always run git init
            # In OSS mode, only run git init if workspace_base is not set
            if self.user_id or not self.config.workspace_base:
                logger.debug(
                    'No repository selected. Initializing a new git repository in the workspace.'
                )
                action = CmdRunAction(
                    command=f'git init && git config --global --add safe.directory {self.workspace_root}'
                )
                self.run_action(action)
            else:
                logger.info(
                    'In workspace mount mode, not initializing a new git repository.'
                )
            return ''

        remote_repo_url = await self._get_authenticated_git_url(
            selected_repository, git_provider_tokens
        )

        if not remote_repo_url:
            raise ValueError('Missing either Git token or valid repository')

        if self.status_callback:
            self.status_callback(
                'info', 'STATUS$SETTING_UP_WORKSPACE', 'Setting up workspace...'
            )

        dir_name = selected_repository.split('/')[-1]

        # Generate a random branch name to avoid conflicts
        random_str = ''.join(
            random.choices(string.ascii_lowercase + string.digits, k=8)
        )
        openhands_workspace_branch = f'openhands-workspace-{random_str}'

        # Clone repository command
        clone_command = f'git clone {remote_repo_url} {dir_name}'

        # Checkout to appropriate branch
        checkout_command = (
            f'git checkout {selected_branch}'
            if selected_branch
            else f'git checkout -b {openhands_workspace_branch}'
        )

        clone_action = CmdRunAction(command=clone_command)
        self.run_action(clone_action)

        cd_checkout_action = CmdRunAction(
            command=f'cd {dir_name} && {checkout_command}'
        )
        action = cd_checkout_action
        self.log('info', f'Cloning repo: {selected_repository}')
        self.run_action(action)
        return dir_name

    def maybe_run_setup_script(self):
        """Run .openhands/setup.sh if it exists in the workspace or repository."""
        setup_script = '.openhands/setup.sh'
        read_obs = self.read(FileReadAction(path=setup_script))
        if isinstance(read_obs, ErrorObservation):
            return

        if self.status_callback:
            self.status_callback(
                'info', 'STATUS$SETTING_UP_WORKSPACE', 'Setting up workspace...'
            )

        # setup scripts time out after 10 minutes
        action = CmdRunAction(
            f'chmod +x {setup_script} && source {setup_script}', blocking=True
        )
        action.set_hard_timeout(600)
        obs = self.run_action(action)
        if not isinstance(obs, CmdOutputObservation) or obs.exit_code != 0:
            self.log('error', f'Setup script failed: {obs.content}')

    @property
    def workspace_root(self) -> Path:
        """Return the workspace root path."""
        return Path(self.config.workspace_mount_path_in_sandbox)

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

    def _load_microagents_from_directory(
        self, microagents_dir: Path, source_description: str
    ) -> list[BaseMicroagent]:
        """Load microagents from a directory.

        Args:
            microagents_dir: Path to the directory containing microagents
            source_description: Description of the source for logging purposes

        Returns:
            A list of loaded microagents
        """
        loaded_microagents: list[BaseMicroagent] = []
        files = self.list_files(str(microagents_dir))

        if not files:
            return loaded_microagents

        self.log(
            'info',
            f'Found {len(files)} files in {source_description} microagents directory',
        )
        zip_path = self.copy_from(str(microagents_dir))
        microagent_folder = tempfile.mkdtemp()

        try:
            with ZipFile(zip_path, 'r') as zip_file:
                zip_file.extractall(microagent_folder)

            zip_path.unlink()
            repo_agents, knowledge_agents = load_microagents_from_dir(microagent_folder)

            self.log(
                'info',
                f'Loaded {len(repo_agents)} repo agents and {len(knowledge_agents)} knowledge agents from {source_description}',
            )

            loaded_microagents.extend(repo_agents.values())
            loaded_microagents.extend(knowledge_agents.values())
        finally:
            shutil.rmtree(microagent_folder)

        return loaded_microagents

    async def _get_authenticated_git_url(
        self, repo_name: str, git_provider_tokens: PROVIDER_TOKEN_TYPE | None
    ) -> str:
        """Get an authenticated git URL for a repository.

        Args:
            repo_path: Repository name (owner/repo)

        Returns:
            Authenticated git URL if credentials are available, otherwise regular HTTPS URL
        """

        try:
            provider_handler = ProviderHandler(
                git_provider_tokens or MappingProxyType({})
            )
            repository = await provider_handler.verify_repo_provider(repo_name)
        except AuthenticationError:
            raise Exception('Git provider authentication issue when getting remote URL')

        provider = repository.git_provider
        repo_name = repository.full_name

        provider_domains = {
            ProviderType.GITHUB: 'github.com',
            ProviderType.GITLAB: 'gitlab.com',
            ProviderType.BITBUCKET: 'bitbucket.org',
        }

        domain = provider_domains[provider]

        # If git_provider_tokens is provided, use the host from the token if available
        if git_provider_tokens and provider in git_provider_tokens:
            domain = git_provider_tokens[provider].host or domain

        # Try to use token if available, otherwise use public URL
        if git_provider_tokens and provider in git_provider_tokens:
            git_token = git_provider_tokens[provider].token
            if git_token:
                token_value = git_token.get_secret_value()
                if provider == ProviderType.GITLAB:
                    remote_url = (
                        f'https://oauth2:{token_value}@{domain}/{repo_name}.git'
                    )
                elif provider == ProviderType.BITBUCKET:
                    # For Bitbucket, handle username:app_password format
                    if ':' in token_value:
                        # App token format: username:app_password
                        remote_url = f'https://{token_value}@{domain}/{repo_name}.git'
                    else:
                        # Access token format: use x-token-auth
                        remote_url = f'https://x-token-auth:{token_value}@{domain}/{repo_name}.git'
                else:
                    # GitHub
                    remote_url = f'https://{token_value}@{domain}/{repo_name}.git'
            else:
                remote_url = f'https://{domain}/{repo_name}.git'
        else:
            remote_url = f'https://{domain}/{repo_name}.git'

        return remote_url

    def get_microagents_from_org_or_user(
        self, selected_repository: str
    ) -> list[BaseMicroagent]:
        """Load microagents from the organization or user level .openhands repository.

        For example, if the repository is github.com/acme-co/api, this will check if
        github.com/acme-co/.openhands exists. If it does, it will clone it and load
        the microagents from the ./microagents/ folder.

        Args:
            selected_repository: The repository path (e.g., "github.com/acme-co/api")

        Returns:
            A list of loaded microagents from the org/user level repository
        """
        loaded_microagents: list[BaseMicroagent] = []

        repo_parts = selected_repository.split('/')
        if len(repo_parts) < 2:
            return loaded_microagents

        # Extract the domain and org/user name
        org_name = repo_parts[-2]

        # Construct the org-level .openhands repo path
        org_openhands_repo = f'{org_name}/.openhands'

        self.log(
            'info',
            f'Checking for org-level microagents at {org_openhands_repo}',
        )

        # Try to clone the org-level .openhands repo
        try:
            # Create a temporary directory for the org-level repo
            org_repo_dir = self.workspace_root / f'org_openhands_{org_name}'

            # Get authenticated URL and do a shallow clone (--depth 1) for efficiency
            try:
                remote_url = call_async_from_sync(
                    self._get_authenticated_git_url,
                    GENERAL_TIMEOUT,
                    org_openhands_repo,
                    self.git_provider_tokens,
                )
            except Exception as e:
                raise Exception(str(e))
            clone_cmd = (
                f'GIT_TERMINAL_PROMPT=0 git clone --depth 1 {remote_url} {org_repo_dir}'
            )

            action = CmdRunAction(command=clone_cmd)
            obs = self.run_action(action)

            if isinstance(obs, CmdOutputObservation) and obs.exit_code == 0:
                self.log(
                    'info',
                    f'Successfully cloned org-level microagents from {org_openhands_repo}',
                )

                # Load microagents from the org-level repo
                org_microagents_dir = org_repo_dir / 'microagents'
                loaded_microagents = self._load_microagents_from_directory(
                    org_microagents_dir, 'org-level'
                )

                # Clean up the org repo directory
                shutil.rmtree(org_repo_dir)
            else:
                self.log(
                    'info',
                    f'No org-level microagents found at {org_openhands_repo}',
                )

        except Exception as e:
            self.log('error', f'Error loading org-level microagents: {str(e)}')

        return loaded_microagents

    def get_microagents_from_selected_repo(
        self, selected_repository: str | None
    ) -> list[BaseMicroagent]:
        """Load microagents from the selected repository.
        If selected_repository is None, load microagents from the current workspace.
        This is the main entry point for loading microagents.

        This method also checks for user/org level microagents stored in a .openhands repository.
        For example, if the repository is github.com/acme-co/api, it will also check for
        github.com/acme-co/.openhands and load microagents from there if it exists.
        """
        loaded_microagents: list[BaseMicroagent] = []
        microagents_dir = self.workspace_root / '.openhands' / 'microagents'
        repo_root = None

        # Check for user/org level microagents if a repository is selected
        if selected_repository:
            # Load microagents from the org/user level repository
            org_microagents = self.get_microagents_from_org_or_user(selected_repository)
            loaded_microagents.extend(org_microagents)

            # Continue with repository-specific microagents
            repo_root = self.workspace_root / selected_repository.split('/')[-1]
            microagents_dir = repo_root / '.openhands' / 'microagents'

        self.log(
            'info',
            f'Selected repo: {selected_repository}, loading microagents from {microagents_dir} (inside runtime)',
        )

        # Legacy Repo Instructions
        # Check for legacy .openhands_instructions file
        obs = self.read(
            FileReadAction(path=str(self.workspace_root / '.openhands_instructions'))
        )
        if isinstance(obs, ErrorObservation) and repo_root is not None:
            # If the instructions file is not found in the workspace root, try to load it from the repo root
            self.log(
                'debug',
                f'.openhands_instructions not present, trying to load from repository {microagents_dir=}',
            )
            obs = self.read(
                FileReadAction(path=str(repo_root / '.openhands_instructions'))
            )

        if isinstance(obs, FileReadObservation):
            self.log('info', 'openhands_instructions microagent loaded.')
            loaded_microagents.append(
                BaseMicroagent.load(
                    path='.openhands_instructions',
                    microagent_dir=None,
                    file_content=obs.content,
                )
            )

        # Load microagents from directory
        repo_microagents = self._load_microagents_from_directory(
            microagents_dir, 'repository'
        )
        loaded_microagents.extend(repo_microagents)

        return loaded_microagents

    def run_action(self, action: Action) -> Observation:
        """Run an action and return the resulting observation.
        If the action is not runnable in any runtime, a NullObservation is returned.
        If the action is not supported by the current runtime, an ErrorObservation is returned.
        """
        if not action.runnable:
            if isinstance(action, AgentThinkAction):
                return AgentThinkObservation('Your thought has been logged.')
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

    @abstractmethod
    def get_mcp_config(
        self, extra_stdio_servers: list[MCPStdioServerConfig] | None = None
    ) -> MCPConfig:
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
    def edit(self, action: FileEditAction) -> Observation:
        pass

    @abstractmethod
    def browse(self, action: BrowseURLAction) -> Observation:
        pass

    @abstractmethod
    def browse_interactive(self, action: BrowseInteractiveAction) -> Observation:
        pass

    @abstractmethod
    async def call_tool_mcp(self, action: MCPAction) -> Observation:
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
    # Authentication
    # ====================================================================

    @property
    def session_api_key(self) -> str | None:
        return None

    # ====================================================================
    # VSCode
    # ====================================================================

    @property
    def vscode_enabled(self) -> bool:
        return self._vscode_enabled

    @property
    def vscode_url(self) -> str | None:
        raise NotImplementedError('This method is not implemented in the base class.')

    @property
    def web_hosts(self) -> dict[str, int]:
        return {}

    # ====================================================================
    # Git
    # ====================================================================

    def _execute_shell_fn_git_handler(
        self, command: str, cwd: str | None
    ) -> CommandResult:
        """
        This function is used by the GitHandler to execute shell commands.
        """
        obs = self.run(CmdRunAction(command=command, is_static=True, cwd=cwd))
        exit_code = 0
        content = ''

        if isinstance(obs, ErrorObservation):
            exit_code = -1

        if hasattr(obs, 'exit_code'):
            exit_code = obs.exit_code
        if hasattr(obs, 'content'):
            content = obs.content

        return CommandResult(content=content, exit_code=exit_code)

    def get_git_changes(self, cwd: str) -> list[dict[str, str]] | None:
        self.git_handler.set_cwd(cwd)
        return self.git_handler.get_git_changes()

    def get_git_diff(self, file_path: str, cwd: str) -> dict[str, str]:
        self.git_handler.set_cwd(cwd)
        return self.git_handler.get_git_diff(file_path)

    @property
    def additional_agent_instructions(self) -> str:
        return ''

    def subscribe_to_shell_stream(
        self, callback: Callable[[str], None] | None = None
    ) -> bool:
        """
        Subscribe to shell command output stream.
        This method is meant to be overridden by runtime implementations
        that want to stream shell command output to external consumers.

        Args:
            callback: A function that will be called with each line of output from shell commands.
                     If None, any existing subscription will be removed.

        Returns False by default.
        """
        return False
