from fastapi import FastAPI
from fastapi.security import HTTPBearer
from openhands.server.config import config, session_manager
from openhands.server.middleware import LocalhostCORSMiddleware, NoCacheMiddleware, attach_session
from openhands.server.websocket import websocket_endpoint
from openhands.server.api_options import router as api_options_router
from openhands.server.api_files import router as api_files_router

app = FastAPI()
app.add_middleware(
    LocalhostCORSMiddleware,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)
app.add_middleware(NoCacheMiddleware)
app.middleware('http')(attach_session)
app.websocket('/ws')(websocket_endpoint)
app.include_router(api_options_router, prefix='/api/options')
app.include_router(api_files_router, prefix='/api')

security_scheme = HTTPBearer()

async def list_files(request: Request, path: str | None = None):
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


def sanitize_filename(filename):
    """Sanitize the filename to prevent directory traversal"""
    # Remove any directory components
    filename = os.path.basename(filename)
    # Remove any non-alphanumeric characters except for .-_
    filename = re.sub(r'[^\w\-_\.]', '', filename)
    # Limit the filename length
    max_length = 255
    if len(filename) > max_length:
        name, ext = os.path.splitext(filename)
        filename = name[: max_length - len(ext)] + ext
    return filename


@app.post('/api/upload-files')
async def upload_file(request: Request, files: list[UploadFile]):
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


@app.get('/api/defaults')
async def appconfig_defaults():
    """Retrieve the default configuration settings.

    To get the default configurations:
    ```sh
    curl http://localhost:3000/api/defaults
    ```

    Returns:
        dict: The default configuration settings.
    """
    return config.defaults_dict


@app.post('/api/save-file')
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


@app.route('/api/security/{path:path}', methods=['GET', 'POST', 'PUT', 'DELETE'])
async def security_api(request: Request):
    """Catch-all route for security analyzer API requests.

    Each request is handled directly to the security analyzer.

    Args:
        request (Request): The incoming FastAPI request object.

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


@app.get('/api/zip-directory')
async def zip_current_workspace(request: Request, background_tasks: BackgroundTasks):
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


class AuthCode(BaseModel):
    code: str


@app.post('/api/github/callback')
def github_callback(auth_code: AuthCode):
    # Prepare data for the token exchange request
    data = {
        'client_id': GITHUB_CLIENT_ID,
        'client_secret': GITHUB_CLIENT_SECRET,
        'code': auth_code.code,
    }

    logger.debug('Exchanging code for GitHub token')

    headers = {'Accept': 'application/json'}
    response = requests.post(
        'https://github.com/login/oauth/access_token', data=data, headers=headers
    )

    if response.status_code != 200:
        logger.error(f'Failed to exchange code for token: {response.text}')
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={'error': 'Failed to exchange code for token'},
        )

    token_response = response.json()

    if 'access_token' not in token_response:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={'error': 'No access token in response'},
        )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={'access_token': token_response['access_token']},
    )


@app.post('/api/authenticate')
async def authenticate(request: Request):
    token = request.headers.get('X-GitHub-Token')
    if not await authenticate_github_user(token):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={'error': 'Not authorized via GitHub waitlist'},
        )

    # Create a signed JWT token with 1-hour expiration
    cookie_data = {
        'github_token': token,
        'exp': int(time.time()) + 3600,  # 1 hour expiration
    }
    signed_token = sign_token(cookie_data, config.jwt_secret)

    response = JSONResponse(
        status_code=status.HTTP_200_OK, content={'message': 'User authenticated'}
    )

    # Set secure cookie with signed token
    response.set_cookie(
        key='github_auth',
        value=signed_token,
        max_age=3600,  # 1 hour in seconds
        httponly=True,
        secure=True,
        samesite='strict',
    )
    return response


class SPAStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        try:
            return await super().get_response(path, scope)
        except Exception:
            # FIXME: just making this HTTPException doesn't work for some reason
            return await super().get_response('index.html', scope)


app.mount('/', SPAStaticFiles(directory='./frontend/build', html=True), name='dist')
