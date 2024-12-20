import os
import tempfile

from fastapi import (
    APIRouter,
    BackgroundTasks,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse, JSONResponse
from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern

from openhands.core.exceptions import AgentRuntimeUnavailableError
from openhands.core.logger import openhands_logger as logger
from openhands.events.action import (
    FileReadAction,
    FileWriteAction,
)
from openhands.events.observation import (
    ErrorObservation,
    FileReadObservation,
    FileWriteObservation,
)
from openhands.runtime.base import Runtime
from openhands.server.file_config import (
    FILES_TO_IGNORE,
    MAX_FILE_SIZE_MB,
    is_extension_allowed,
    sanitize_filename,
)
from openhands.utils.async_utils import call_sync_from_async

app = APIRouter(prefix='/api/conversations/{conversation_id}')


@app.get('/list-files')
async def list_files(request: Request, conversation_id: str, path: str | None = None):
    """List files in the specified path.

    This function retrieves a list of files from the agent's runtime file store,
    excluding certain system and hidden files/directories.

    To list files:
    ```sh
    curl http://localhost:3000/api/list-files
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
        logger.error(f'Error listing files: {e}', exc_info=True)
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
        logger.error(f'Error filtering files: {e}', exc_info=True)
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
    curl http://localhost:3000/api/select-file?file=<file_path>
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
        logger.error(f'Error opening file {file}: {e}', exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={'error': f'Error opening file: {e}'},
        )

    if isinstance(observation, FileReadObservation):
        content = observation.content
        return {'code': content}
    elif isinstance(observation, ErrorObservation):
        logger.error(f'Error opening file {file}: {observation}', exc_info=False)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={'error': f'Error opening file: {observation}'},
        )


@app.post('/upload-files')
async def upload_file(request: Request, conversation_id: str, files: list[UploadFile]):
    """Upload a list of files to the workspace.

    To upload a files:
    ```sh
    curl -X POST -F "file=@<file_path1>" -F "file=@<file_path2>" http://localhost:3000/api/upload-files
    ```

    Args:
        request (Request): The incoming request object.
        files (list[UploadFile]): A list of files to be uploaded.

    Returns:
        dict: A message indicating the success of the upload operation.

    Raises:
        HTTPException: If there's an error saving the files.
    """
    try:
        uploaded_files = []
        skipped_files = []
        for file in files:
            safe_filename = sanitize_filename(file.filename)
            file_contents = await file.read()

            if (
                MAX_FILE_SIZE_MB > 0
                and len(file_contents) > MAX_FILE_SIZE_MB * 1024 * 1024
            ):
                skipped_files.append(
                    {
                        'name': safe_filename,
                        'reason': f'Exceeds maximum size limit of {MAX_FILE_SIZE_MB}MB',
                    }
                )
                continue

            if not is_extension_allowed(safe_filename):
                skipped_files.append(
                    {'name': safe_filename, 'reason': 'File type not allowed'}
                )
                continue

            # copy the file to the runtime
            with tempfile.TemporaryDirectory() as tmp_dir:
                tmp_file_path = os.path.join(tmp_dir, safe_filename)
                with open(tmp_file_path, 'wb') as tmp_file:
                    tmp_file.write(file_contents)
                    tmp_file.flush()

                runtime: Runtime = request.state.conversation.runtime
                try:
                    await call_sync_from_async(
                        runtime.copy_to,
                        tmp_file_path,
                        runtime.config.workspace_mount_path_in_sandbox,
                    )
                except AgentRuntimeUnavailableError as e:
                    logger.error(
                        f'Error saving file {safe_filename}: {e}', exc_info=True
                    )
                    return JSONResponse(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        content={'error': f'Error saving file: {e}'},
                    )
            uploaded_files.append(safe_filename)

        response_content = {
            'message': 'File upload process completed',
            'uploaded_files': uploaded_files,
            'skipped_files': skipped_files,
        }

        if not uploaded_files and skipped_files:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    **response_content,
                    'error': 'No files were uploaded successfully',
                },
            )

        return JSONResponse(status_code=status.HTTP_200_OK, content=response_content)

    except Exception as e:
        logger.error(f'Error during file upload: {e}', exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                'error': f'Error during file upload: {str(e)}',
                'uploaded_files': [],
                'skipped_files': [],
            },
        )


@app.post('/save-file')
async def save_file(request: Request):
    """Save a file to the agent's runtime file store.

    This endpoint allows saving a file when the agent is in a paused, finished,
    or awaiting user input state. It checks the agent's state before proceeding
    with the file save operation.

    Args:
        request (Request): The incoming FastAPI request object.

    Returns:
        JSONResponse: A JSON response indicating the success of the operation.

    Raises:
        HTTPException:
            - 403 error if the agent is not in an allowed state for editing.
            - 400 error if the file path or content is missing.
            - 500 error if there's an unexpected error during the save operation.
    """
    try:
        # Extract file path and content from the request
        data = await request.json()
        file_path = data.get('filePath')
        content = data.get('content')

        # Validate the presence of required data
        if not file_path or content is None:
            raise HTTPException(status_code=400, detail='Missing filePath or content')

        # Save the file to the agent's runtime file store
        runtime: Runtime = request.state.conversation.runtime
        file_path = os.path.join(
            runtime.config.workspace_mount_path_in_sandbox, file_path
        )
        write_action = FileWriteAction(file_path, content)
        try:
            observation = await call_sync_from_async(runtime.run_action, write_action)
        except AgentRuntimeUnavailableError as e:
            logger.error(f'Error saving file: {e}', exc_info=True)
            return JSONResponse(
                status_code=500,
                content={'error': f'Error saving file: {e}'},
            )

        if isinstance(observation, FileWriteObservation):
            return JSONResponse(
                status_code=200, content={'message': 'File saved successfully'}
            )
        elif isinstance(observation, ErrorObservation):
            return JSONResponse(
                status_code=500,
                content={'error': f'Failed to save file: {observation}'},
            )
        else:
            return JSONResponse(
                status_code=500,
                content={'error': f'Unexpected observation: {observation}'},
            )
    except Exception as e:
        # Log the error and return a 500 response
        logger.error(f'Error saving file: {e}', exc_info=True)
        raise HTTPException(status_code=500, detail=f'Error saving file: {e}')


@app.get('/zip-directory')
async def zip_current_workspace(
    request: Request, conversation_id: str, background_tasks: BackgroundTasks
):
    try:
        logger.debug('Zipping workspace')
        runtime: Runtime = request.state.conversation.runtime
        path = runtime.config.workspace_mount_path_in_sandbox
        try:
            zip_file = await call_sync_from_async(runtime.copy_from, path)
        except AgentRuntimeUnavailableError as e:
            logger.error(f'Error zipping workspace: {e}', exc_info=True)
            return JSONResponse(
                status_code=500,
                content={'error': f'Error zipping workspace: {e}'},
            )
        response = FileResponse(
            path=zip_file,
            filename='workspace.zip',
            media_type='application/x-zip-compressed',
        )

        # This will execute after the response is sent (So the file is not deleted before being sent)
        background_tasks.add_task(zip_file.unlink)

        return response
    except Exception as e:
        logger.error(f'Error zipping workspace: {e}', exc_info=True)
        raise HTTPException(
            status_code=500,
            detail='Failed to zip workspace',
        )
