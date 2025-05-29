import base64
import os

import aiofiles  # type: ignore
from fastapi import (
    APIRouter,
    HTTPException,
    Request,
    status,
)
from fastapi.responses import FileResponse, JSONResponse
from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern
from pydantic import BaseModel
from starlette.background import BackgroundTask

from openhands.core.config import load_app_config
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
from openhands.server.file_config import (
    FILES_TO_IGNORE,
)
from openhands.server.shared import (
    s3_handler,
)
from openhands.utils.async_utils import call_sync_from_async


def safe_base64_decode(data: str) -> bytes:
    try:
        # Remove any whitespace and newlines
        data = data.strip().replace('\n', '').replace('\r', '')

        # Add padding if necessary
        missing_padding = len(data) % 4
        if missing_padding:
            data += '=' * (4 - missing_padding)

        return base64.b64decode(data)
    except Exception as e:
        raise ValueError(f'Invalid base64 data: {e}')


def safe_base64_encode(data: bytes) -> str:
    return base64.b64encode(data).decode('utf-8')


app = APIRouter(prefix='/api/conversations/{conversation_id}')
config_app = load_app_config()


class UploadFileRequest(BaseModel):
    file: str


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

    workspace_path = runtime.config.workspace_mount_path_in_sandbox or ''
    raw_file = file
    file = os.path.join(workspace_path + '/' + runtime.sid, file)
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
            try:
                workspace_base = config_app.workspace_base or ''
                openhand_file_path = os.path.join(
                    workspace_base + '/' + runtime.sid, raw_file
                )
                async with aiofiles.open(openhand_file_path, 'rb') as f:
                    binary_data = await f.read()
                    base64_encoded = safe_base64_encode(binary_data)
                    return {'code': base64_encoded}
            except Exception as e:
                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content={'error': f'Error reading binary file: {e}'},
                )
        else:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={'error': f'Error opening file: {observation}'},
            )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={'error': f'Error opening file: {observation}'},
    )


@app.post('/upload-image-file')
async def uploadImageFile(request: Request, data: UploadFileRequest):
    file = data.file
    file_parts = file.split('.')
    if len(file_parts) < 2:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={'error': 'Invalid file type'},
        )
    ext = file_parts[-1]
    if ext not in ['png', 'jpg', 'jpeg', 'gif', 'webp']:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={'error': 'Invalid file type'},
        )
    runtime: Runtime = request.state.conversation.runtime
    workspace_path = runtime.config.workspace_mount_path_in_sandbox or ''
    file_path = os.path.join(workspace_path + '/' + runtime.sid, file)
    read_action = FileReadAction(file_path)
    image_raw_data: bytes | None = None
    try:
        observation = await call_sync_from_async(runtime.run_action, read_action)
    except AgentRuntimeUnavailableError as e:
        logger.error(f'Error opening file {file}: {e}')
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={'error': f'Error opening file: {e}'},
        )
    if isinstance(observation, FileReadObservation):
        file_content = observation.content
        try:
            # Handle different content formats
            if file_content.startswith('data:image/'):
                # Data URL format: "data:image/png;base64,iVBORw0KGgo..."
                base64_part = (
                    file_content.split(',', 1)[1]
                    if ',' in file_content
                    else file_content
                )
                image_raw_data = safe_base64_decode(base64_part)
            else:
                # Try to decode as plain base64
                image_raw_data = safe_base64_decode(file_content)

        except ValueError as e:
            logger.error(f'Error decoding base64 content: {e}')
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={'error': f'Invalid base64 content: {e}'},
            )
    elif isinstance(observation, ErrorObservation):
        logger.error(f'Error opening file {file}: {observation}')

        if 'ERROR_BINARY_FILE' in observation.message:
            try:
                workspace_base = config_app.workspace_base or ''
                openhand_file_path = os.path.join(
                    workspace_base + '/' + runtime.sid, file
                )
                async with aiofiles.open(openhand_file_path, 'rb') as f:
                    binary_data = await f.read()
                    image_raw_data = binary_data
            except Exception as e:
                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content={'error': f'Error reading binary file: {e}'},
                )
        else:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={'error': f'Error opening file: {observation}'},
            )

    if image_raw_data:
        folder_path = f'workspace/{runtime.sid}'
        s3_url = await s3_handler.upload_raw_file(image_raw_data, folder_path, file)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={'message': 'File uploaded successfully', 'url': s3_url},
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={'error': 'Failed to read image data'},
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
