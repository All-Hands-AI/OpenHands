

from abc import ABC
import os
from pathlib import Path
import tempfile
import base62

from dataclasses import dataclass
import logging
from typing import AsyncGenerator
from openhands.app_server.app_conversation.app_conversation_models import AppConversationStartTask, AppConversationStartTaskStatus
from openhands.app_server.app_conversation.app_conversation_service import AppConversationService

from openhands.sdk import RemoteWorkspace

from openhands.app_server.sandbox.sandbox_models import SandboxInfo
from openhands.app_server.user.user_service import UserService

_logger = logging.getLogger(__name__)
PRE_COMMIT_HOOK = '.git/hooks/pre-commit'
PRE_COMMIT_LOCAL = '.git/hooks/pre-commit.local'


@dataclass
class GitAppConversationService(AppConversationService, ABC):
    """ App Conversation service which adds git specific functionality.

    Sets up repositories and installs hooks """

    init_git_in_empty_workspace: bool
    user_service: UserService

    async def run_setup_scripts(
        self,
        task: AppConversationStartTask,
        workspace: RemoteWorkspace,
    ) -> AsyncGenerator[AppConversationStartTask, None]:
        task.status = AppConversationStartTaskStatus.PREPARING_REPOSITORY
        await self.clone_or_init_git_repo(task, workspace)
        yield task

        task.status = AppConversationStartTaskStatus.RUNNING_SETUP_SCRIPT
        await self.maybe_run_setup_script(workspace)
        yield task

        task.status = AppConversationStartTaskStatus.SETTING_UP_GIT_HOOKS
        await self.maybe_setup_git_hooks(workspace)
        yield task

    async def clone_or_init_git_repo(
        self,
        task: AppConversationStartTask,
        workspace: RemoteWorkspace,
    ):
        request = task.request

        if not request.selected_repository:
            if self.init_git_in_empty_workspace:
                _logger.debug('Initializing a new git repository in the workspace.')
                await workspace.execute_command(
                    'git init && git config --global --add safe.directory ' +
                    workspace.working_dir
                )
            else:
                _logger.info('Not initializing a new git repository.')
            return

        remote_repo_url: str = await self.user_service.get_authenticated_git_url(
            request.selected_repository
        )
        if not remote_repo_url:
            raise ValueError('Missing either Git token or valid repository')

        dir_name = request.selected_repository.split('/')[-1]

        # Clone the repo - this is the slow part!
        clone_command = f'git clone {remote_repo_url} {dir_name}'
        await workspace.execute_command(clone_command, workspace.working_dir)

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
        workspace: RemoteWorkspace,
    ):
        """Run .openhands/setup.sh if it exists in the workspace or repository."""
        setup_script = workspace.working_dir + '/.openhands/setup.sh'

        await workspace.execute_command(f'chmod +x {setup_script} && source {setup_script}', timeout=600)

        #TODO: Does this need to be done?
        # Add the action to the event stream as an ENVIRONMENT event
        #source = EventSource.ENVIRONMENT
        #self.event_stream.add_event(action, source)

    async def maybe_setup_git_hooks(
        self,
        workspace: RemoteWorkspace,
    ):
        """Set up git hooks if .openhands/pre-commit.sh exists in the workspace or repository."""
        command = (
            'mkdir -p .git/hooks && '
            f'chmod +x .openhands/pre-commit.sh'
        )
        result = await workspace.execute_command(command, workspace.working_dir)
        if result['exit_code']:
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
                    result = await workspace.execute_command(command, workspace.working_dir)
                    if result.get('exit_code') != 0:
                        _logger.error(
                            f'Failed to preserve existing pre-commit hook: {result.get('stderr')}',
                        )
                        return

        # write the pre-commit hook
        await workspace.file_upload(
            src_path=Path(__file__).parent / "pre-commit.sh",
            destination_path=PRE_COMMIT_HOOK,
        )

        # Make the pre-commit hook executable
        result = await workspace.execute_command(f'chmod +x {PRE_COMMIT_HOOK}')
        if result.get('exit_code'):
            _logger.error(f'Failed to make pre-commit hook executable: {result.get('stderr')}')
            return

        _logger.info('Git pre-commit hook installed successfully')
