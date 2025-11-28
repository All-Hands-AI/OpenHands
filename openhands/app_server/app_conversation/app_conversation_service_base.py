import logging
import os
import tempfile
from abc import ABC
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, AsyncGenerator

if TYPE_CHECKING:
    from openhands.core.config.openhands_config import OpenHandsConfig
from urllib.parse import urlparse

import base62

from openhands.app_server.app_conversation.app_conversation_models import (
    AppConversationStartTask,
    AppConversationStartTaskStatus,
)
from openhands.app_server.app_conversation.app_conversation_service import (
    AppConversationService,
)
from openhands.app_server.app_conversation.skill_loader import (
    load_global_skills,
    load_repo_skills,
    load_sandbox_skills,
    merge_skills,
)
from openhands.app_server.sandbox.sandbox_models import SandboxInfo
from openhands.app_server.user.user_context import UserContext
from openhands.core.config.mcp_config import (
    MCPSHTTPServerConfig,
    MCPStdioServerConfig,
    OpenHandsMCPConfigImpl,
)
from openhands.sdk import Agent
from openhands.sdk.context.agent_context import AgentContext
from openhands.sdk.context.skills import load_user_skills
from openhands.sdk.workspace.remote.async_remote_workspace import AsyncRemoteWorkspace

_logger = logging.getLogger(__name__)
PRE_COMMIT_HOOK = '.git/hooks/pre-commit'
PRE_COMMIT_LOCAL = '.git/hooks/pre-commit.local'


@dataclass
class AppConversationServiceBase(AppConversationService, ABC):
    """App Conversation service which adds git specific functionality.

    Sets up repositories and installs hooks"""

    init_git_in_empty_workspace: bool
    user_context: UserContext

    async def _load_and_merge_all_skills(
        self,
        sandbox: SandboxInfo,
        remote_workspace: AsyncRemoteWorkspace,
        selected_repository: str | None,
        working_dir: str,
    ) -> list:
        """Load skills from all sources and merge them.

        This method handles all errors gracefully and will return an empty list
        if skill loading fails completely.

        Args:
            remote_workspace: AsyncRemoteWorkspace for loading repo skills
            selected_repository: Repository name or None
            working_dir: Working directory path

        Returns:
            List of merged Skill objects from all sources, or empty list on failure
        """
        try:
            _logger.debug('Loading skills for V1 conversation')

            # Load skills from all sources
            sandbox_skills = load_sandbox_skills(sandbox)
            global_skills = load_global_skills()
            # Load user skills from ~/.openhands/skills/ directory
            # Uses the SDK's load_user_skills() function which handles loading from
            # ~/.openhands/skills/ and ~/.openhands/microagents/ (for backward compatibility)
            try:
                user_skills = load_user_skills()
                _logger.info(
                    f'Loaded {len(user_skills)} user skills: {[s.name for s in user_skills]}'
                )
            except Exception as e:
                _logger.warning(f'Failed to load user skills: {str(e)}')
                user_skills = []
            repo_skills = await load_repo_skills(
                remote_workspace, selected_repository, working_dir
            )

            # Merge all skills (later lists override earlier ones)
            all_skills = merge_skills(
                [sandbox_skills, global_skills, user_skills, repo_skills]
            )

            _logger.info(
                f'Loaded {len(all_skills)} total skills: {[s.name for s in all_skills]}'
            )

            return all_skills
        except Exception as e:
            _logger.warning(f'Failed to load skills: {e}', exc_info=True)
            # Return empty list on failure - skills will be loaded again later if needed
            return []

    def _convert_mcp_config_to_sdk_format(
        self,
        shttp_servers: list[MCPSHTTPServerConfig],
        stdio_servers: list[MCPStdioServerConfig],
    ) -> dict[str, dict[str, Any]]:
        """Convert OpenHands MCP config format to SDK's expected format.

        Args:
            shttp_servers: List of SHTTP MCP server configs
            stdio_servers: List of stdio MCP server configs

        Returns:
            Dictionary in SDK's mcp_config format: {"mcpServers": {...}}
        """
        mcp_servers: dict[str, dict[str, Any]] = {}

        # Convert SHTTP servers to HTTP transport format
        for idx, shttp_server in enumerate(shttp_servers):
            # Use a descriptive name for the first server, numbered for subsequent ones
            if idx == 0:
                server_name = 'openhands'
            else:
                server_name = f'openhands_{idx}'
            server_config: dict[str, Any] = {
                'transport': 'http',
                'url': shttp_server.url,
            }
            if shttp_server.api_key:
                server_config['headers'] = {
                    'Authorization': f'Bearer {shttp_server.api_key}'
                }
            mcp_servers[server_name] = server_config

        # Convert stdio servers to stdio transport format
        for stdio_server in stdio_servers:
            stdio_server_config: dict[str, Any] = {
                'transport': 'stdio',
                'command': stdio_server.command,
                'args': stdio_server.args,
            }
            if stdio_server.env:
                stdio_server_config['env'] = stdio_server.env
            mcp_servers[stdio_server.name] = stdio_server_config

        return {'mcpServers': mcp_servers}

    def _load_openhands_config_with_search_key(
        self, search_api_key: str | None, app_mode: str | None = None
    ) -> 'OpenHandsConfig | None':  # type: ignore[name-defined]
        """Load OpenHandsConfig and merge user's search_api_key if provided.

        In SaaS mode, returns None immediately as the config is not needed.
        In OSS mode, loads the config and merges the user's search_api_key.

        Args:
            search_api_key: Optional user's search API key from settings.
                          If provided, will be merged into the config.
            app_mode: Optional app mode. If 'saas', returns None immediately.

        Returns:
            OpenHandsConfig with merged search_api_key, or None if SaaS mode or loading fails.
        """
        # In SaaS mode, config is not needed for MCP setup
        if app_mode == 'saas':
            _logger.debug(
                'SaaS mode detected, skipping OpenHandsConfig load for MCP setup'
            )
            return None

        try:
            from pydantic import SecretStr

            from openhands.core.config.utils import load_openhands_config

            openhands_config = load_openhands_config(set_logging_levels=False)
            # Merge user's search_api_key into the config if provided
            # This mirrors V0's behavior: self.config.search_api_key = settings.search_api_key
            # The user's search_api_key from settings.json needs to be in the config
            # for add_search_engine() to detect and add the Tavily search engine
            if search_api_key and openhands_config:
                openhands_config = openhands_config.model_copy(
                    update={'search_api_key': SecretStr(search_api_key)}
                )
                _logger.debug(
                    'Merged user search_api_key into OpenHandsConfig for MCP setup'
                )
            return openhands_config
        except Exception as e:
            _logger.debug(
                f'Could not load OpenHandsConfig for MCP setup: {e}. '
                'This is expected in SaaS mode where config is not needed.'
            )
            return None

    def _add_openhands_mcp_config_to_agent(
        self,
        agent: Agent,
        web_url: str | None,
        user_id: str | None = None,
        search_api_key: str | None = None,
        app_mode: str | None = None,
    ) -> Agent:
        """Add OpenHands MCP server configuration to an agent.

        Uses OpenHandsMCPConfigImpl to create the MCP server configuration, which
        handles SaaS mode API key generation and other environment-specific logic.

        Args:
            agent: The agent to update with MCP configuration
            web_url: The web URL where the OpenHands MCP server is accessible.
                    If None, the agent is returned unchanged.
            user_id: Optional user ID for MCP API key generation (required in SaaS mode).
            search_api_key: Optional user's search API key from settings.
                          If provided, will be merged into the config for search engine detection.
            app_mode: Optional app mode. If 'saas', config loading is skipped.

        Returns:
            Updated agent with OpenHands MCP server configuration, or the original
            agent if web_url is None or configuration fails.
        """
        if not web_url:
            return agent

        try:
            # Extract host from web_url (hostname:port format)
            # This matches what OpenHandsMCPConfigImpl.create_default_mcp_server_config expects
            parsed_url = urlparse(web_url)
            host = parsed_url.netloc
            if not host:
                _logger.warning(f'Could not extract host from web_url: {web_url}')
                return agent

            # Load OpenHandsConfig for OSS mode (needed for search engine detection)
            # In SaaS mode, this returns None immediately
            openhands_config = self._load_openhands_config_with_search_key(
                search_api_key, app_mode
            )

            # Use OpenHandsMCPConfigImpl to create MCP server config
            # This handles both OSS and SaaS scenarios (API key generation, search MCP, etc.)
            # Pass None for config if we couldn't load it - SaaS implementation doesn't use it
            openhands_mcp_server, stdio_servers = (
                OpenHandsMCPConfigImpl.create_default_mcp_server_config(
                    host,
                    openhands_config,  # type: ignore[arg-type]
                    user_id,
                )
            )

            if not openhands_mcp_server:
                _logger.warning(
                    'OpenHandsMCPConfigImpl did not return an MCP server config. '
                    'Falling back to direct web_url construction.'
                )
                # Fallback to direct web_url construction (legacy behavior)
                if not parsed_url.scheme:
                    _logger.warning(
                        f'Unable to construct MCP server URL from web_url: {web_url}'
                    )
                    return agent

                openhands_mcp_server = MCPSHTTPServerConfig(
                    url=f'{parsed_url.scheme}://{host}/mcp/mcp',
                    api_key=None,
                )
                stdio_servers = []

            # Convert to SDK format
            sdk_mcp_config = self._convert_mcp_config_to_sdk_format(
                [openhands_mcp_server], stdio_servers
            )

            # Merge with existing mcp_config if any
            existing_mcp_config = agent.mcp_config or {}
            existing_servers = existing_mcp_config.get('mcpServers', {})
            sdk_mcp_config['mcpServers'].update(existing_servers)

            # Create a new agent instance with updated mcp_config
            # Since AgentBase is frozen, we use model_copy to create a new instance
            agent = agent.model_copy(update={'mcp_config': sdk_mcp_config})
            _logger.info(
                f'Added OpenHands MCP server to agent: {openhands_mcp_server.url}'
            )
            return agent
        except Exception as e:
            _logger.warning(
                f'Failed to add OpenHands MCP server configuration: {e}',
                exc_info=True,
            )
            # Continue without MCP config - don't fail conversation startup
            return agent

    def _create_agent_with_skills(self, agent, skills: list):
        """Create or update agent with skills in its context.

        Args:
            agent: The agent to update
            skills: List of Skill objects to add to agent context

        Returns:
            Updated agent with skills in context
        """
        if agent.agent_context:
            # Merge with existing context
            existing_skills = agent.agent_context.skills
            all_skills = merge_skills([skills, existing_skills])
            agent = agent.model_copy(
                update={
                    'agent_context': agent.agent_context.model_copy(
                        update={'skills': all_skills}
                    )
                }
            )
        else:
            # Create new context
            agent_context = AgentContext(skills=skills)
            agent = agent.model_copy(update={'agent_context': agent_context})

        return agent

    async def _load_skills_and_update_agent(
        self,
        sandbox: SandboxInfo,
        agent: Agent,
        remote_workspace: AsyncRemoteWorkspace,
        selected_repository: str | None,
        working_dir: str,
    ):
        """Load all skills and update agent with them.

        Args:
            agent: The agent to update
            remote_workspace: AsyncRemoteWorkspace for loading repo skills
            selected_repository: Repository name or None
            working_dir: Working directory path

        Returns:
            Updated agent with skills loaded into context
        """
        # Load and merge all skills
        all_skills = await self._load_and_merge_all_skills(
            sandbox, remote_workspace, selected_repository, working_dir
        )

        # Update agent with skills
        agent = self._create_agent_with_skills(agent, all_skills)

        return agent

    async def run_setup_scripts(
        self,
        task: AppConversationStartTask,
        sandbox: SandboxInfo,
        workspace: AsyncRemoteWorkspace,
    ) -> AsyncGenerator[AppConversationStartTask, None]:
        task.status = AppConversationStartTaskStatus.PREPARING_REPOSITORY
        yield task
        await self.clone_or_init_git_repo(task, workspace)

        task.status = AppConversationStartTaskStatus.RUNNING_SETUP_SCRIPT
        yield task
        await self.maybe_run_setup_script(workspace)

        task.status = AppConversationStartTaskStatus.SETTING_UP_GIT_HOOKS
        yield task
        await self.maybe_setup_git_hooks(workspace)

        task.status = AppConversationStartTaskStatus.SETTING_UP_SKILLS
        yield task
        await self._load_and_merge_all_skills(
            sandbox,
            workspace,
            task.request.selected_repository,
            workspace.working_dir,
        )

    async def clone_or_init_git_repo(
        self,
        task: AppConversationStartTask,
        workspace: AsyncRemoteWorkspace,
    ):
        request = task.request

        # Create the projects directory if it does not exist yet
        parent = Path(workspace.working_dir).parent
        result = await workspace.execute_command(
            f'mkdir {workspace.working_dir}', parent
        )
        if result.exit_code:
            _logger.warning(f'mkdir failed: {result.stderr}')

        if not request.selected_repository:
            if self.init_git_in_empty_workspace:
                _logger.debug('Initializing a new git repository in the workspace.')
                cmd = (
                    'git init && git config --global '
                    f'--add safe.directory {workspace.working_dir}'
                )
                result = await workspace.execute_command(cmd, workspace.working_dir)
                if result.exit_code:
                    _logger.warning(f'Git init failed: {result.stderr}')
            else:
                _logger.info('Not initializing a new git repository.')
            return

        remote_repo_url: str = await self.user_context.get_authenticated_git_url(
            request.selected_repository
        )
        if not remote_repo_url:
            raise ValueError('Missing either Git token or valid repository')

        dir_name = request.selected_repository.split('/')[-1]

        # Clone the repo - this is the slow part!
        clone_command = f'git clone {remote_repo_url} {dir_name}'
        result = await workspace.execute_command(clone_command, workspace.working_dir)
        if result.exit_code:
            _logger.warning(f'Git clone failed: {result.stderr}')

        # Checkout the appropriate branch
        if request.selected_branch:
            checkout_command = f'git checkout {request.selected_branch}'
        else:
            # Generate a random branch name to avoid conflicts
            random_str = base62.encodebytes(os.urandom(16))
            openhands_workspace_branch = f'openhands-workspace-{random_str}'
            checkout_command = f'git checkout -b {openhands_workspace_branch}'
        await workspace.execute_command(checkout_command, workspace.working_dir)

    async def maybe_run_setup_script(
        self,
        workspace: AsyncRemoteWorkspace,
    ):
        """Run .openhands/setup.sh if it exists in the workspace or repository."""
        setup_script = workspace.working_dir + '/.openhands/setup.sh'

        await workspace.execute_command(
            f'chmod +x {setup_script} && source {setup_script}', timeout=600
        )

        # TODO: Does this need to be done?
        # Add the action to the event stream as an ENVIRONMENT event
        # source = EventSource.ENVIRONMENT
        # self.event_stream.add_event(action, source)

    async def maybe_setup_git_hooks(
        self,
        workspace: AsyncRemoteWorkspace,
    ):
        """Set up git hooks if .openhands/pre-commit.sh exists in the workspace or repository."""
        command = 'mkdir -p .git/hooks && chmod +x .openhands/pre-commit.sh'
        result = await workspace.execute_command(command, workspace.working_dir)
        if result.exit_code:
            return

        # Check if there's an existing pre-commit hook
        with tempfile.TemporaryFile(mode='w+t') as temp_file:
            result = workspace.file_download(PRE_COMMIT_HOOK, str(temp_file))
            if result.get('success'):
                _logger.info('Preserving existing pre-commit hook')
                # an existing pre-commit hook exists
                if 'This hook was installed by OpenHands' not in temp_file.read():
                    # Move the existing hook to pre-commit.local
                    command = (
                        f'mv {PRE_COMMIT_HOOK} {PRE_COMMIT_LOCAL} &&'
                        f'chmod +x {PRE_COMMIT_LOCAL}'
                    )
                    result = await workspace.execute_command(
                        command, workspace.working_dir
                    )
                    if result.exit_code != 0:
                        _logger.error(
                            f'Failed to preserve existing pre-commit hook: {result.stderr}',
                        )
                        return

        # write the pre-commit hook
        await workspace.file_upload(
            source_path=Path(__file__).parent / 'git' / 'pre-commit.sh',
            destination_path=PRE_COMMIT_HOOK,
        )

        # Make the pre-commit hook executable
        result = await workspace.execute_command(f'chmod +x {PRE_COMMIT_HOOK}')
        if result.exit_code:
            _logger.error(f'Failed to make pre-commit hook executable: {result.stderr}')
            return

        _logger.info('Git pre-commit hook installed successfully')
