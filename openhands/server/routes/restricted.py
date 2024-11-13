import os
import tempfile
from typing import Callable

import jwt
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
from openhands.events.serialization import event_to_dict
from openhands.events.stream import AsyncEventStreamWrapper
from openhands.runtime.base import Runtime
from openhands.server.auth.auth import get_sid_from_token
from openhands.server.data_models.feedback import FeedbackDataModel, store_feedback
from openhands.server.file_config import (
    FILES_TO_IGNORE,
    MAX_FILE_SIZE_MB,
    is_extension_allowed,
    sanitize_filename,
)
from openhands.server.github import (
    UserVerifier,
)
from openhands.server.shared import config, session_manager
from openhands.utils.async_utils import call_sync_from_async

app = APIRouter()


class AttachSessionMiddleware:
    def __init__(self, app, target_router: APIRouter):
        self.app = app
        self.target_router = target_router
        self.target_paths = {route.path for route in target_router.routes}
        self.prefix = target_router.prefix or ''

    async def __call__(self, request: Request, call_next: Callable):
        do_attach = False
        current_path = request.url.path
        if current_path.startswith(self.prefix):
            path_without_prefix = current_path[len(self.prefix) :]
        else:
            path_without_prefix = current_path
        if not path_without_prefix.startswith('/'):
            path_without_prefix = '/' + path_without_prefix
        if path_without_prefix in self.target_paths:
            do_attach = True

        if request.method == 'OPTIONS':
            do_attach = False

        if not do_attach:
            return await call_next(request)

        user_verifier = UserVerifier()
        if user_verifier.is_active():
            signed_token = request.cookies.get('github_auth')
            if not signed_token:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={'error': 'Not authenticated'},
                )
            try:
                jwt.decode(signed_token, config.jwt_secret, algorithms=['HS256'])
            except Exception as e:
                logger.warning(f'Invalid token: {e}')
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={'error': 'Invalid token'},
                )

        if not request.headers.get('Authorization'):
            logger.warning('Missing Authorization header')
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={'error': 'Missing Authorization header'},
            )

        auth_token = request.headers.get('Authorization')
        if 'Bearer' in auth_token:
            auth_token = auth_token.split('Bearer')[1].strip()

        request.state.sid = get_sid_from_token(auth_token, config.jwt_secret)
        if request.state.sid == '':
            logger.warning('Invalid token')
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={'error': 'Invalid token'},
            )

        request.state.conversation = await session_manager.attach_to_conversation(
            request.state.sid
        )
        if request.state.conversation is None:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={'error': 'Session not found'},
            )
        try:
            response = await call_next(request)
        finally:
            await session_manager.detach_from_conversation(request.state.conversation)
        return response


@app.get('/api/list-files')
async def list_files(
    request: Request,
    path: str | None = None,
):
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
    file_list = await call_sync_from_async(runtime.list_files, path)
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

    file_list = await filter_for_gitignore(file_list, '')

    return file_list


@app.get('/api/select-file')
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
    observation = await call_sync_from_async(runtime.run_action, read_action)

    if isinstance(observation, FileReadObservation):
        content = observation.content
        return {'code': content}
    elif isinstance(observation, ErrorObservation):
        logger.error(f'Error opening file {file}: {observation}', exc_info=False)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={'error': f'Error opening file: {observation}'},
        )


@app.post('/api/upload-files')
async def upload_file(
    request: Request,
    files: list[UploadFile],
):
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
                runtime.copy_to(
                    tmp_file_path, runtime.config.workspace_mount_path_in_sandbox
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


@app.post('/api/save-file')
async def save_file(request: Request):
    """Save a file to the agent's runtime file store.

    This endpoint allows saving a file when the agent is in a paused, finished,
    or awaiting user input state. It checks the agent's state before proceeding
    with the file save operation.

    Args:
        request (Request): The incoming APIRouter request object.

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
        observation = await call_sync_from_async(runtime.run_action, write_action)

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


@app.post('/api/submit-feedback')
async def submit_feedback(request: Request):
    """Submit user feedback.

    This function stores the provided feedback data.

    To submit feedback:
    ```sh
    curl -X POST -d '{"email": "test@example.com"}' -H "Authorization:"
    ```

    Args:
        request (Request): The incoming request object.
        feedback (FeedbackDataModel): The feedback data to be stored.

    Returns:
        dict: The stored feedback data.

    Raises:
        HTTPException: If there's an error submitting the feedback.
    """
    # Assuming the storage service is already configured in the backend
    # and there is a function to handle the storage.
    body = await request.json()
    async_stream = AsyncEventStreamWrapper(
        request.state.conversation.event_stream, filter_hidden=True
    )
    trajectory = []
    async for event in async_stream:
        trajectory.append(event_to_dict(event))
    feedback = FeedbackDataModel(
        email=body.get('email', ''),
        version=body.get('version', ''),
        permissions=body.get('permissions', 'private'),
        polarity=body.get('polarity', ''),
        feedback=body.get('polarity', ''),
        trajectory=trajectory,
    )
    try:
        feedback_data = await call_sync_from_async(store_feedback, feedback)
        return JSONResponse(status_code=200, content=feedback_data)
    except Exception as e:
        logger.error(f'Error submitting feedback: {e}')
        return JSONResponse(
            status_code=500, content={'error': 'Failed to submit feedback'}
        )


@app.get('/api/zip-directory')
async def zip_current_workspace(
    request: Request,
    background_tasks: BackgroundTasks,
):
    try:
        logger.debug('Zipping workspace')
        runtime: Runtime = request.state.conversation.runtime
        path = runtime.config.workspace_mount_path_in_sandbox
        zip_file = await call_sync_from_async(runtime.copy_from, path)
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


@app.route('/api/security/{path:path}', methods=['GET', 'POST', 'PUT', 'DELETE'])
async def security_api(request: Request):
    """Catch-all route for security analyzer API requests.

    Each request is handled directly to the security analyzer.

    Args:
        request (Request): The incoming APIRouter request object.

    Returns:
        Any: The response from the security analyzer.

    Raises:
        HTTPException: If the security analyzer is not initialized.
    """
    if not request.state.conversation.security_analyzer:
        raise HTTPException(status_code=404, detail='Security analyzer not initialized')

    return await request.state.conversation.security_analyzer.handle_api_request(
        request
    )


@app.get('/api/vscode-url')
async def get_vscode_url(request: Request):
    """Get the VSCode URL.

    This endpoint allows getting the VSCode URL.

    Args:
        request (Request): The incoming APIRouter request object.

    Returns:
        JSONResponse: A JSON response indicating the success of the operation.
    """
    try:
        runtime: Runtime = request.state.conversation.runtime
        logger.debug(f'Runtime type: {type(runtime)}')
        logger.debug(f'Runtime VSCode URL: {runtime.vscode_url}')
        return JSONResponse(status_code=200, content={'vscode_url': runtime.vscode_url})
    except Exception as e:
        logger.error(f'Error getting VSCode URL: {e}', exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                'vscode_url': None,
                'error': f'Error getting VSCode URL: {e}',
            },
        )
