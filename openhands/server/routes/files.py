import os
import re
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    status,
)
from fastapi.responses import FileResponse, JSONResponse
from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern
from pydantic import BaseModel
from starlette.background import BackgroundTask

from openhands.core.exceptions import AgentRuntimeUnavailableError
from openhands.core.logger import openhands_logger as logger
from openhands.events.action import (
    CmdRunAction,
    FileReadAction,
)
from openhands.events.observation import (
    CmdOutputObservation,
    ErrorObservation,
    FileReadObservation,
)
from openhands.runtime.base import Runtime
from openhands.server.data_models.conversation_info import ConversationInfo
from openhands.server.file_config import (
    FILES_TO_IGNORE,
)
from openhands.server.shared import (
    ConversationStoreImpl,
    config,
    conversation_manager,
)
from openhands.server.user_auth import get_user_id
from openhands.server.utils import get_conversation_store
from openhands.storage.conversation.conversation_store import ConversationStore
from openhands.storage.data_models.conversation_metadata import ConversationMetadata
from openhands.storage.data_models.conversation_status import ConversationStatus
from openhands.utils.async_utils import call_sync_from_async

class CommitState(str, Enum):
    """Enum representing the state of git commits in a repository."""
    CLEAN = "CLEAN"  # No changes, current commit matches origin commit for the same branch
    IN_PROGRESS = "IN_PROGRESS"  # There are uncommitted changes or local commits not in origin


class GitInfoResponse(BaseModel):
    """Response model for git information."""
    branch: Optional[str] = None
    repository: Optional[str] = None
    commit_state: Optional[CommitState] = None
    error: Optional[str] = None


app = APIRouter(prefix='/api/conversations/{conversation_id}')


@app.get('/list-files')
async def list_files(request: Request, path: str | None = None):
    """List files in the specified path.

    This function retrieves a list of files from the agent's runtime file store,
    excluding certain system and hidden files/directories.

    To list files:
    ```sh
    curl http://localhost:3000/api/conversations/{conversation_id}/list-files
    ```

    Args:
        request (Request): The incoming request object.
        path (str, optional): The path to list files from. Defaults to None.

    Returns:
        list: A list of file names in the specified path.

    Raises:
        HTTPException: If there's an error listing the files.
    """
    if not request.state.conversation.runtime:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={'error': 'Runtime not yet initialized'},
        )

    runtime: Runtime = request.state.conversation.runtime
    try:
        file_list = await call_sync_from_async(runtime.list_files, path)
    except AgentRuntimeUnavailableError as e:
        logger.error(f'Error listing files: {e}')
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={'error': f'Error listing files: {e}'},
        )
    if path:
        file_list = [os.path.join(path, f) for f in file_list]

    file_list = [f for f in file_list if f not in FILES_TO_IGNORE]

    async def filter_for_gitignore(file_list, base_path):
        gitignore_path = os.path.join(base_path, '.gitignore')
        try:
            read_action = FileReadAction(gitignore_path)
            observation = await call_sync_from_async(runtime.run_action, read_action)
            spec = PathSpec.from_lines(
                GitWildMatchPattern, observation.content.splitlines()
            )
        except Exception as e:
            logger.warning(e)
            return file_list
        file_list = [entry for entry in file_list if not spec.match_file(entry)]
        return file_list

    try:
        file_list = await filter_for_gitignore(file_list, '')
    except AgentRuntimeUnavailableError as e:
        logger.error(f'Error filtering files: {e}')
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={'error': f'Error filtering files: {e}'},
        )

    return file_list


@app.get('/select-file')
async def select_file(file: str, request: Request):
    """Retrieve the content of a specified file.

    To select a file:
    ```sh
    curl http://localhost:3000/api/conversations/{conversation_id}select-file?file=<file_path>
    ```

    Args:
        file (str): The path of the file to be retrieved.
            Expect path to be absolute inside the runtime.
        request (Request): The incoming request object.

    Returns:
        dict: A dictionary containing the file content.

    Raises:
        HTTPException: If there's an error opening the file.
    """
    runtime: Runtime = request.state.conversation.runtime

    file = os.path.join(runtime.config.workspace_mount_path_in_sandbox, file)
    read_action = FileReadAction(file)
    try:
        observation = await call_sync_from_async(runtime.run_action, read_action)
    except AgentRuntimeUnavailableError as e:
        logger.error(f'Error opening file {file}: {e}')
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={'error': f'Error opening file: {e}'},
        )

    if isinstance(observation, FileReadObservation):
        content = observation.content
        return {'code': content}
    elif isinstance(observation, ErrorObservation):
        logger.error(f'Error opening file {file}: {observation}')

        if 'ERROR_BINARY_FILE' in observation.message:
            return JSONResponse(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                content={'error': f'Unable to open binary file: {file}'},
            )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={'error': f'Error opening file: {observation}'},
        )


@app.get('/zip-directory')
def zip_current_workspace(request: Request):
    try:
        logger.debug('Zipping workspace')
        runtime: Runtime = request.state.conversation.runtime
        path = runtime.config.workspace_mount_path_in_sandbox
        try:
            zip_file_path = runtime.copy_from(path)
        except AgentRuntimeUnavailableError as e:
            logger.error(f'Error zipping workspace: {e}')
            return JSONResponse(
                status_code=500,
                content={'error': f'Error zipping workspace: {e}'},
            )
        return FileResponse(
            path=zip_file_path,
            filename='workspace.zip',
            media_type='application/zip',
            background=BackgroundTask(lambda: os.unlink(zip_file_path)),
        )
    except Exception as e:
        logger.error(f'Error zipping workspace: {e}')
        raise HTTPException(
            status_code=500,
            detail='Failed to zip workspace',
        )


@app.get('/git/changes')
async def git_changes(
    request: Request,
    conversation_id: str,
    user_id: str = Depends(get_user_id),
):
    runtime: Runtime = request.state.conversation.runtime
    conversation_store = await ConversationStoreImpl.get_instance(
        config,
        user_id,
    )

    cwd = await get_cwd(
        conversation_store,
        conversation_id,
        runtime.config.workspace_mount_path_in_sandbox,
    )
    logger.info(f'Getting git changes in {cwd}')

    try:
        changes = await call_sync_from_async(runtime.get_git_changes, cwd)
        if changes is None:
            return JSONResponse(
                status_code=404,
                content={'error': 'Not a git repository'},
            )
        return changes
    except AgentRuntimeUnavailableError as e:
        logger.error(f'Runtime unavailable: {e}')
        return JSONResponse(
            status_code=500,
            content={'error': f'Error getting changes: {e}'},
        )
    except Exception as e:
        logger.error(f'Error getting changes: {e}')
        return JSONResponse(
            status_code=500,
            content={'error': str(e)},
        )


@app.get('/git/diff')
async def git_diff(
    request: Request,
    path: str,
    conversation_id: str,
    conversation_store = Depends(get_conversation_store),
):
    runtime: Runtime = request.state.conversation.runtime

    cwd = await get_cwd(
        conversation_store,
        conversation_id,
        runtime.config.workspace_mount_path_in_sandbox,
    )

    try:
        diff = await call_sync_from_async(runtime.get_git_diff, path, cwd)
        return diff
    except AgentRuntimeUnavailableError as e:
        logger.error(f'Error getting diff: {e}')
        return JSONResponse(
            status_code=500,
            content={'error': f'Error getting diff: {e}'},
        )


@app.get('/git/branch')
async def git_branch(
    request: Request,
    conversation_id: str,
    conversation_store = Depends(get_conversation_store),
):
    """Get the current git branch for the conversation's repository.
    
    Returns:
        dict: A dictionary containing the current branch name.
        
    Raises:
        HTTPException: If there's an error getting the branch or if not a git repository.
    """
    runtime: Runtime = request.state.conversation.runtime

    cwd = await get_cwd(
        conversation_store,
        conversation_id,
        runtime.config.workspace_mount_path_in_sandbox,
    )
    
    try:
        # Check if it's a git repository first
        cmd_action = CmdRunAction(command='git rev-parse --is-inside-work-tree', cwd=cwd)
        result = await call_sync_from_async(runtime.run_action, cmd_action)
        
        if not isinstance(result, CmdOutputObservation) or result.exit_code != 0 or result.content.strip() != 'true':
            return JSONResponse(
                status_code=404,
                content={'error': 'Not a git repository'},
            )
            
        # Get the current branch
        cmd_action = CmdRunAction(command='git rev-parse --abbrev-ref HEAD', cwd=cwd)
        result = await call_sync_from_async(runtime.run_action, cmd_action)
        
        if not isinstance(result, CmdOutputObservation) or result.exit_code != 0:
            return JSONResponse(
                status_code=500,
                content={'error': 'Failed to get current branch'},
            )
            
        return {'branch': result.content.strip()}
    except AgentRuntimeUnavailableError as e:
        logger.error(f'Runtime unavailable: {e}')
        return JSONResponse(
            status_code=500,
            content={'error': f'Error getting branch: {e}'},
        )
    except Exception as e:
        logger.error(f'Error getting branch: {e}')
        return JSONResponse(
            status_code=500,
            content={'error': str(e)},
        )


@app.post('/git/update-info')
async def update_git_info(
    request: Request,
    conversation_id: str,
    user_id: str = Depends(get_user_id),
):
    """Update and retrieve git information for the conversation's repository.
    
    This endpoint:
    1. Retrieves the current branch
    2. Retrieves the remote repository URL
    3. Determines the commit state (CLEAN or IN_PROGRESS)
    4. Updates the conversation metadata with the branch and repository
    5. Returns all the information as JSON
    
    Returns:
        GitInfoResponse: A JSON object containing branch, repository, and commit state information.
        
    Raises:
        HTTPException: If there's an error retrieving git information or if not a git repository.
    """
    runtime: Runtime = request.state.conversation.runtime
    conversation_store = await ConversationStoreImpl.get_instance(
        config,
        user_id,
    )

    cwd = await get_cwd(
        conversation_store,
        conversation_id,
        runtime.config.workspace_mount_path_in_sandbox,
    )
    
    response = GitInfoResponse()
    
    try:
        # Check if it's a git repository first
        cmd_action = CmdRunAction(command='git rev-parse --is-inside-work-tree', cwd=cwd)
        result = await call_sync_from_async(runtime.run_action, cmd_action)
        
        if not isinstance(result, CmdOutputObservation) or result.exit_code != 0 or result.content.strip() != 'true':
            response.error = 'Not a git repository'
            return response
        
        # Get current branch
        cmd_action = CmdRunAction(command='git rev-parse --abbrev-ref HEAD', cwd=cwd)
        branch_result = await call_sync_from_async(runtime.run_action, cmd_action)
        
        if not isinstance(branch_result, CmdOutputObservation) or branch_result.exit_code != 0:
            response.error = 'Failed to get current branch'
            return response
        
        current_branch = branch_result.content.strip()
        response.branch = current_branch
        
        # Get remote repository URL
        cmd_action = CmdRunAction(command='git remote -v', cwd=cwd)
        remote_result = await call_sync_from_async(runtime.run_action, cmd_action)
        
        repository = None
        if isinstance(remote_result, CmdOutputObservation) and remote_result.exit_code == 0:
            # Parse the remote URL to extract the repository
            remote_output = remote_result.content.strip()
            if remote_output:
                # Look for GitHub or GitLab URLs
                match = re.search(r'(github\.com|gitlab\.com)[:/]([^/\s]+/[^/\s]+)(?:\.git|\s)', remote_output)
                if match:
                    repository = match.group(2)
                    response.repository = repository
        
        # Check for uncommitted changes
        cmd_action = CmdRunAction(command='git status --porcelain', cwd=cwd)
        status_result = await call_sync_from_async(runtime.run_action, cmd_action)
        
        if not isinstance(status_result, CmdOutputObservation) or status_result.exit_code != 0:
            response.error = 'Failed to check git status'
            return response
        
        # If there are uncommitted changes, set state to IN_PROGRESS
        if status_result.content.strip():
            response.commit_state = CommitState.IN_PROGRESS
        else:
            # Check if there are commits not pushed to origin
            cmd_action = CmdRunAction(
                command=f'git rev-list HEAD...origin/{current_branch} --count 2>/dev/null || echo "0"', 
                cwd=cwd
            )
            unpushed_result = await call_sync_from_async(runtime.run_action, cmd_action)
            
            if not isinstance(unpushed_result, CmdOutputObservation):
                response.error = 'Failed to check unpushed commits'
                return response
            
            # If there are unpushed commits, set state to IN_PROGRESS
            if unpushed_result.content.strip() != '0':
                response.commit_state = CommitState.IN_PROGRESS
            else:
                # If we got here, everything is clean
                response.commit_state = CommitState.CLEAN
        
        # Update the conversation metadata with the branch and repository
        try:
            metadata = await conversation_store.get_metadata(conversation_id)
            
            # Only update if we have new information
            updated = False
            if current_branch and metadata.selected_branch != current_branch:
                metadata.selected_branch = current_branch
                updated = True
                
            if repository and metadata.selected_repository != repository:
                metadata.selected_repository = repository
                updated = True
                
            if updated:
                metadata.last_updated_at = datetime.now(timezone.utc)
                await conversation_store.save_metadata(metadata)
                logger.info(f"Updated metadata for conversation {conversation_id} with branch={current_branch}, repository={repository}")
        except Exception as e:
            logger.error(f"Failed to update conversation metadata: {e}")
            # Don't fail the request if metadata update fails
            response.error = f"Retrieved git info but failed to update metadata: {str(e)}"
        
        return response
    except AgentRuntimeUnavailableError as e:
        logger.error(f'Runtime unavailable: {e}')
        response.error = f'Error getting git info: {e}'
        return response
    except Exception as e:
        logger.error(f'Error getting git info: {e}')
        response.error = str(e)
        return response


@app.get('/git/commit-state')
async def git_commit_state(
    request: Request,
    conversation_id: str,
    conversation_store = Depends(get_conversation_store),
):
    """Get the commit state for the conversation's repository.
    
    Returns:
        dict: A dictionary containing the commit state (CLEAN or IN_PROGRESS).
        
    Raises:
        HTTPException: If there's an error getting the commit state or if not a git repository.
    """
    runtime: Runtime = request.state.conversation.runtime

    cwd = await get_cwd(
        conversation_store,
        conversation_id,
        runtime.config.workspace_mount_path_in_sandbox,
    )
    
    try:
        # Check if it's a git repository first
        cmd_action = CmdRunAction(command='git rev-parse --is-inside-work-tree', cwd=cwd)
        result = await call_sync_from_async(runtime.run_action, cmd_action)
        
        if not isinstance(result, CmdOutputObservation) or result.exit_code != 0 or result.content.strip() != 'true':
            return JSONResponse(
                status_code=404,
                content={'error': 'Not a git repository'},
            )
            
        # Check for uncommitted changes
        cmd_action = CmdRunAction(command='git status --porcelain', cwd=cwd)
        result = await call_sync_from_async(runtime.run_action, cmd_action)
        
        if not isinstance(result, CmdOutputObservation) or result.exit_code != 0:
            return JSONResponse(
                status_code=500,
                content={'error': 'Failed to check git status'},
            )
            
        # If there are uncommitted changes, return IN_PROGRESS
        if result.content.strip():
            return {'state': CommitState.IN_PROGRESS}
            
        # Get current branch
        cmd_action = CmdRunAction(command='git rev-parse --abbrev-ref HEAD', cwd=cwd)
        branch_result = await call_sync_from_async(runtime.run_action, cmd_action)
        
        if not isinstance(branch_result, CmdOutputObservation) or branch_result.exit_code != 0:
            return JSONResponse(
                status_code=500,
                content={'error': 'Failed to get current branch'},
            )
        
        current_branch = branch_result.content.strip()
        
        # Check if there are commits not pushed to origin
        cmd_action = CmdRunAction(
            command=f'git rev-list HEAD...origin/{current_branch} --count 2>/dev/null || echo "0"', 
            cwd=cwd
        )
        result = await call_sync_from_async(runtime.run_action, cmd_action)
        
        if not isinstance(result, CmdOutputObservation):
            return JSONResponse(
                status_code=500,
                content={'error': 'Failed to check unpushed commits'},
            )
        
        # If there are unpushed commits, return IN_PROGRESS
        if result.content.strip() != '0':
            return {'state': CommitState.IN_PROGRESS}
            
        # If we got here, everything is clean
        return {'state': CommitState.CLEAN}
    except AgentRuntimeUnavailableError as e:
        logger.error(f'Runtime unavailable: {e}')
        return JSONResponse(
            status_code=500,
            content={'error': f'Error getting commit state: {e}'},
        )
    except Exception as e:
        logger.error(f'Error getting commit state: {e}')
        return JSONResponse(
            status_code=500,
            content={'error': str(e)},
        )


async def get_cwd(
    conversation_store: ConversationStore,
    conversation_id: str,
    workspace_mount_path_in_sandbox: str,
):
    metadata = await conversation_store.get_metadata(conversation_id)
    is_running = await conversation_manager.is_agent_loop_running(conversation_id)
    conversation_info = await _get_conversation_info(metadata, is_running)

    cwd = workspace_mount_path_in_sandbox
    if conversation_info and conversation_info.selected_repository:
        repo_dir = conversation_info.selected_repository.split('/')[-1]
        cwd = os.path.join(cwd, repo_dir)

    return cwd


async def _get_conversation_info(
    conversation: ConversationMetadata,
    is_running: bool,
) -> ConversationInfo | None:
    try:
        title = conversation.title
        if not title:
            title = f'Conversation {conversation.conversation_id[:5]}'
        return ConversationInfo(
            conversation_id=conversation.conversation_id,
            title=title,
            last_updated_at=conversation.last_updated_at,
            created_at=conversation.created_at,
            selected_repository=conversation.selected_repository,
            status=ConversationStatus.RUNNING
            if is_running
            else ConversationStatus.STOPPED,
        )
    except Exception as e:
        logger.error(
            f'Error loading conversation {conversation.conversation_id}: {str(e)}',
            extra={'session_id': conversation.conversation_id},
        )
        return None
