import logging
import os
import tempfile
from abc import ABC
from dataclasses import dataclass
from pathlib import Path
from typing import AsyncGenerator

import base62

from openhands.app_server.app_conversation.app_conversation_models import (
    AppConversationStartTask,
    AppConversationStartTaskStatus,
)
from openhands.app_server.app_conversation.app_conversation_service import (
    AppConversationService,
)
from openhands.app_server.user.user_context import UserContext
from openhands.sdk.workspace.remote.async_remote_workspace import AsyncRemoteWorkspace

_logger = logging.getLogger(__name__)
PRE_COMMIT_HOOK = '.git/hooks/pre-commit'
PRE_COMMIT_LOCAL = '.git/hooks/pre-commit.local'


@dataclass
class GitAppConversationService(AppConversationService, ABC):
    """App Conversation service which adds git specific functionality.

    Sets up repositories and installs hooks"""

    init_git_in_empty_workspace: bool
    user_context: UserContext

    async def run_setup_scripts(
        self,
        task: AppConversationStartTask,
        workspace: AsyncRemoteWorkspace,
        working_dir: str,
    ) -> AsyncGenerator[AppConversationStartTask, None]:
        task.status = AppConversationStartTaskStatus.PREPARING_REPOSITORY
        yield task
        await self.clone_or_init_git_repo(task, workspace, working_dir)

        task.status = AppConversationStartTaskStatus.RUNNING_SETUP_SCRIPT
        yield task
        await self.maybe_run_setup_script(workspace, working_dir)

        task.status = AppConversationStartTaskStatus.SETTING_UP_GIT_HOOKS
        yield task
        await self.maybe_setup_git_hooks(workspace, working_dir)

    async def clone_or_init_git_repo(
        self,
        task: AppConversationStartTask,
        workspace: AsyncRemoteWorkspace,
        working_dir: str,
    ):
        request = task.request

        if not request.selected_repository:
            if self.init_git_in_empty_workspace:
                _logger.debug('Initializing a new git repository in the workspace.')
                await workspace.execute_command(
                    'git init && git config --global --add safe.directory '
                    + working_dir
                )
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
        await workspace.execute_command(clone_command, working_dir)

        # Checkout the appropriate branch
        if request.selected_branch:
            checkout_command = f'git checkout {request.selected_branch}'
        else:
            # Generate a random branch name to avoid conflicts
            random_str = base62.encodebytes(os.urandom(16))
            openhands_workspace_branch = f'openhands-workspace-{random_str}'
            checkout_command = f'git checkout -b {openhands_workspace_branch}'
        await workspace.execute_command(checkout_command, working_dir)

    async def maybe_run_setup_script(
        self,
        workspace: AsyncRemoteWorkspace,
        working_dir: str,
    ):
        """Run .openhands/setup.sh if it exists in the workspace or repository."""
        setup_script = working_dir + '/.openhands/setup.sh'

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
        working_dir: str,
    ):
        """Set up git hooks if .openhands/pre-commit.sh exists in the workspace or repository."""
        command = 'mkdir -p .git/hooks && chmod +x .openhands/pre-commit.sh'
        result = await workspace.execute_command(command, working_dir)
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
                    result = await workspace.execute_command(command, working_dir)
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
