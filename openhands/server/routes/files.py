import os
from typing import Any

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
from starlette.background import BackgroundTask

from openhands.core.exceptions import AgentRuntimeUnavailableError
from openhands.core.logger import openhands_logger as logger
from openhands.events.action import (
    FileReadAction,
)
from openhands.events.observation import (
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

app = APIRouter(prefix='/api/conversations/{conversation_id}')


@app.get(
    '/list-files',
    response_model=list[str],
    responses={
        404: {'description': 'Runtime not initialized', 'model': dict},
        500: {'description': 'Error listing or filtering files', 'model': dict},
    },
)
async def list_files(
    request: Request, path: str | None = None
) -> list[str] | JSONResponse:
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

    async def filter_for_gitignore(file_list: list[str], base_path: str) -> list[str]:
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


# NOTE: We use response_model=None for endpoints that can return multiple response types
# (like FileResponse | JSONResponse). This is because FastAPI's response_model expects a
# Pydantic model, but Starlette response classes like FileResponse are not Pydantic models.
# Instead, we document the possible responses using the 'responses' parameter and maintain
# proper type annotations for mypy.
@app.get(
    '/select-file',
    response_model=None,
    responses={
        200: {'description': 'File content returned as JSON', 'model': dict[str, str]},
        500: {'description': 'Error opening file', 'model': dict},
        415: {'description': 'Unsupported media type', 'model': dict},
    },
)
async def select_file(file: str, request: Request) -> FileResponse | JSONResponse:
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
        return JSONResponse(content={'code': content})
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
    else:
        # Handle unexpected observation types
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={'error': f'Unexpected observation type: {type(observation)}'},
        )


@app.get(
    '/zip-directory',
    response_model=None,
    responses={
        200: {'description': 'Zipped workspace returned as FileResponse'},
        500: {'description': 'Error zipping workspace', 'model': dict},
    },
)
def zip_current_workspace(request: Request) -> FileResponse | JSONResponse:
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


@app.get(
    '/git/changes',
    response_model=list[dict[str, str]],
    responses={
        404: {'description': 'Not a git repository', 'model': dict},
        500: {'description': 'Error getting changes', 'model': dict},
    },
)
async def git_changes(
    request: Request,
    conversation_id: str,
    user_id: str = Depends(get_user_id),
) -> list[dict[str, str]] | JSONResponse:
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


@app.get(
    '/git/diff',
    response_model=dict[str, Any],
    responses={500: {'description': 'Error getting diff', 'model': dict}},
)
async def git_diff(
    request: Request,
    path: str,
    conversation_id: str,
    conversation_store: Any = Depends(get_conversation_store),
) -> dict[str, Any] | JSONResponse:
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


async def get_cwd(
    conversation_store: ConversationStore,
    conversation_id: str,
    workspace_mount_path_in_sandbox: str,
) -> str:
    metadata = await conversation_store.get_metadata(conversation_id)
    cwd = workspace_mount_path_in_sandbox
    if metadata and metadata.selected_repository:
        repo_dir = metadata.selected_repository.split('/')[-1]
        cwd = os.path.join(cwd, repo_dir)

    return cwd
