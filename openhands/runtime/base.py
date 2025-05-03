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

from openhands.core.config import AppConfig, SandboxConfig
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

    async def clone_user_and_org_microagents(
        self,
        git_provider_tokens: PROVIDER_TOKEN_TYPE | None,
        selected_repository: str | None,
    ) -> list[str]:
        """Clone user and organization .openhands repositories if they exist.

        Args:
            git_provider_tokens: Dictionary mapping provider types to tokens
            selected_repository: The repository being worked on

        Returns:
            List of cloned repository names
        """
        cloned_repos: list[str] = []

        if not git_provider_tokens:
            return cloned_repos

        # Get the user
        try:
            provider_handler = ProviderHandler(git_provider_tokens)
            user = await provider_handler.get_user()
            user_name = user.login

            # Try to clone user's .openhands repository
            user_openhands_repo = f'{user_name}/.openhands'
            try:
                # Use the same domain and token as the main repository
                if selected_repository is not None and '/' in selected_repository:
                    provider = None
                    for prov_type in git_provider_tokens:
                        try:
                            service = provider_handler._get_service(prov_type)
                            if selected_repository is not None:
                                await service.get_repository_details_from_repo_name(
                                    selected_repository
                                )
                            provider = prov_type
                            break
                        except Exception:
                            continue

                    if provider:
                        # Clone the user's .openhands repository
                        provider_domains = {
                            ProviderType.GITHUB: 'github.com',
                            ProviderType.GITLAB: 'gitlab.com',
                        }
                        domain = provider_domains[provider]
                        git_token = git_provider_tokens[provider].token

                        if git_token:
                            if provider == ProviderType.GITLAB:
                                remote_repo_url = f'https://oauth2:{git_token.get_secret_value()}@{domain}/{user_openhands_repo}.git'
                            else:
                                remote_repo_url = f'https://{git_token.get_secret_value()}@{domain}/{user_openhands_repo}.git'
                        else:
                            remote_repo_url = (
                                f'https://{domain}/{user_openhands_repo}.git'
                            )

                        # Clone the repository to user-specific directory
                        # Create user directory if it doesn't exist
                        mkdir_command = f'mkdir -p {user_name}'
                        self.run_action(CmdRunAction(command=mkdir_command))

                        # Clone into user directory
                        dir_name = f'{user_name}/.openhands'

                        # Check if directory already exists
                        check_dir_command = (
                            f'[ -d "{dir_name}" ] && echo "exists" || echo "not exists"'
                        )
                        check_obs = self.run_action(
                            CmdRunAction(command=check_dir_command)
                        )

                        if (
                            isinstance(check_obs, CmdOutputObservation)
                            and 'exists' in check_obs.content
                        ):
                            self.log(
                                'info',
                                f"User's .openhands repository already exists at {dir_name}",
                            )
                            cloned_repos.append(user_openhands_repo)
                        else:
                            clone_command = f'git clone {remote_repo_url} {dir_name}'
                            action = CmdRunAction(
                                command=clone_command,
                            )
                            self.log(
                                'info',
                                f'Cloning user microagents repo: {user_openhands_repo}',
                            )
                            obs = self.run_action(action)

                            if (
                                isinstance(obs, CmdOutputObservation)
                                and obs.exit_code == 0
                            ):
                                cloned_repos.append(user_openhands_repo)
                                self.log(
                                    'info',
                                    f"Cloned user's .openhands repository: {user_openhands_repo}",
                                )
            except Exception as e:
                self.log(
                    'debug',
                    f"User doesn't have a .openhands repository or it's not accessible: {e}",
                )

            # If selected repository is from an organization, try to clone org's .openhands repository
            if selected_repository is not None and '/' in selected_repository:
                org_name = selected_repository.split('/')[0]
                # Skip if org_name is the same as user_login (user's own repo)
                if org_name != user_name:
                    org_openhands_repo = f'{org_name}/.openhands'
                    try:
                        # Use the same domain and token as the main repository
                        provider = None
                        for prov_type in git_provider_tokens:
                            try:
                                service = provider_handler._get_service(prov_type)
                                await service.get_repository_details_from_repo_name(
                                    selected_repository
                                )
                                provider = prov_type
                                break
                            except Exception:
                                continue

                        if provider:
                            # Clone the organization's .openhands repository
                            provider_domains = {
                                ProviderType.GITHUB: 'github.com',
                                ProviderType.GITLAB: 'gitlab.com',
                            }
                            domain = provider_domains[provider]
                            git_token = git_provider_tokens[provider].token

                            if git_token:
                                if provider == ProviderType.GITLAB:
                                    remote_repo_url = f'https://oauth2:{git_token.get_secret_value()}@{domain}/{org_openhands_repo}.git'
                                else:
                                    remote_repo_url = f'https://{git_token.get_secret_value()}@{domain}/{org_openhands_repo}.git'
                            else:
                                remote_repo_url = (
                                    f'https://{domain}/{org_openhands_repo}.git'
                                )

                            # Clone the repository to org-specific directory
                            # Create org directory if it doesn't exist
                            mkdir_command = f'mkdir -p {org_name}'
                            self.run_action(CmdRunAction(command=mkdir_command))

                            # Clone into org directory
                            dir_name = f'{org_name}/.openhands'

                            # Check if directory already exists
                            check_dir_command = f'[ -d "{dir_name}" ] && echo "exists" || echo "not exists"'
                            check_obs = self.run_action(
                                CmdRunAction(command=check_dir_command)
                            )

                            if (
                                isinstance(check_obs, CmdOutputObservation)
                                and 'exists' in check_obs.content
                            ):
                                self.log(
                                    'info',
                                    f"Organization's .openhands repository already exists at {dir_name}",
                                )
                                cloned_repos.append(org_openhands_repo)
                            else:
                                clone_command = (
                                    f'git clone {remote_repo_url} {dir_name}'
                                )
                                action = CmdRunAction(
                                    command=clone_command,
                                )
                                self.log(
                                    'info',
                                    f'Cloning organization microagents repo: {org_openhands_repo}',
                                )
                                obs = self.run_action(action)

                                if (
                                    isinstance(obs, CmdOutputObservation)
                                    and obs.exit_code == 0
                                ):
                                    cloned_repos.append(org_openhands_repo)
                                    self.log(
                                        'info',
                                        f"Cloned organization's .openhands repository: {org_openhands_repo}",
                                    )
                    except Exception as e:
                        self.log(
                            'debug',
                            f"Organization doesn't have a .openhands repository or it's not accessible: {e}",
                        )
        except Exception as e:
            self.log(
                'warning',
                f'Failed to get user information or clone .openhands repositories: {e}',
            )

        return cloned_repos

    async def clone_or_init_repo(
        self,
        git_provider_tokens: PROVIDER_TOKEN_TYPE | None,
        selected_repository: str | None,
        selected_branch: str | None,
    ) -> str:
        repository = None
        if selected_repository:  # Determine provider from repo name
            try:
                provider_handler = ProviderHandler(
                    git_provider_tokens or MappingProxyType({})
                )
                repository = await provider_handler.verify_repo_provider(
                    selected_repository
                )
            except AuthenticationError:
                raise RuntimeError(
                    'Git provider authentication issue when cloning repo'
                )

        if not selected_repository:
            # In SaaS mode (indicated by user_id being set), always run git init
            # In OSS mode, only run git init if workspace_base is not set
            if self.user_id or not self.config.workspace_base:
                logger.debug(
                    'No repository selected. Initializing a new git repository in the workspace.'
                )
                action = CmdRunAction(
                    command='git init',
                )
                self.run_action(action)
            else:
                logger.info(
                    'In workspace mount mode, not initializing a new git repository.'
                )

            # Even if no repository is selected, try to clone user's .openhands repository
            # if we have a token
            if git_provider_tokens:
                await self.clone_user_and_org_microagents(git_provider_tokens, None)

            return ''

        # This satisfies mypy because param is optional, but `verify_repo_provider` guarentees this gets populated
        if not repository:
            return ''

        provider = repository.git_provider
        provider_domains = {
            ProviderType.GITHUB: 'github.com',
            ProviderType.GITLAB: 'gitlab.com',
        }

        domain = provider_domains[provider]

        # Try to use token if available, otherwise use public URL
        if git_provider_tokens and provider in git_provider_tokens:
            git_token = git_provider_tokens[provider].token
            if git_token:
                if provider == ProviderType.GITLAB:
                    remote_repo_url = f'https://oauth2:{git_token.get_secret_value()}@{domain}/{selected_repository}.git'
                else:
                    remote_repo_url = f'https://{git_token.get_secret_value()}@{domain}/{selected_repository}.git'
            else:
                remote_repo_url = f'https://{domain}/{selected_repository}.git'
        else:
            remote_repo_url = f'https://{domain}/{selected_repository}.git'

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

        action = CmdRunAction(
            command=f'{clone_command} ; cd {dir_name} ; {checkout_command}',
        )
        self.log('info', f'Cloning repo: {selected_repository}')
        self.run_action(action)

        # After cloning the main repository, clone user and org microagents repositories
        if git_provider_tokens and selected_repository:
            await self.clone_user_and_org_microagents(
                git_provider_tokens, selected_repository
            )

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
        if isinstance(obs, CmdOutputObservation) and obs.exit_code != 0:
            self.log('error', f'Setup script failed: {obs.content}')

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
            # This will include selected_repo_root
            workspace_files = self.list_files(str(workspace_root))
            for user_dir in workspace_files:
                # FIXME Check if user_dir is a directory
                # FIXME Make this a Path, not a string or fix the code below to be better code!
                user_microagents_dir = Path(f'{user_dir} / .openhands / microagents')
                self.log(
                    'info',
                    f'Loading repository microagents from {user_microagents_dir}',
                )
                repo_microagents = self._load_microagents_from_dir(user_microagents_dir)
                loaded_microagents.extend(repo_microagents)
        except Exception as e:
            self.log('debug', f'Error loading microagents from user directories: {e}')

        # Legacy Repo Instructions
        # Check for legacy .openhands_instructions file
        obs: Observation | None = None
        if selected_repo_root is not None:
            # First try to load from the repo root
            obs = self.read(
                FileReadAction(path=str(selected_repo_root / '.openhands_instructions'))
            )

        if selected_repo_root is None or (obs and isinstance(obs, ErrorObservation)):
            # If not found in repo root, try workspace root
            obs = self.read(
                FileReadAction(path=str(workspace_root / '.openhands_instructions'))
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
