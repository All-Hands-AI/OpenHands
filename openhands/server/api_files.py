from fastapi import APIRouter, Request, HTTPException, status
from fastapi.responses import JSONResponse
from openhands.runtime.base import Runtime
from openhands.utils.async_utils import call_sync_from_async
import os

router = APIRouter()

FILES_TO_IGNORE = [
    '.git/',
    '.DS_Store',
    'node_modules/',
    '__pycache__/',
]

@router.get('/list-files')
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

    return [f for f in file_list if not any(ignored in f for ignored in FILES_TO_IGNORE)]
