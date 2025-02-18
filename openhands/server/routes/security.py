from typing import Any
from fastapi import (
    APIRouter,
    HTTPException,
    Request,
)

app = APIRouter(prefix='/api/conversations/{conversation_id}')


@app.route('/security/{path:path}', methods=['GET', 'POST', 'PUT', 'DELETE'])
async def security_api(request: Request) -> dict[str, Any]:
    """Catch-all route for security analyzer API requests.

    Each request is handled directly to the security analyzer.

    Args:
        request (Request): The incoming FastAPI request object.

    Returns:
        dict[str, Any]: The response from the security analyzer.

    Raises:
        HTTPException: If the security analyzer is not initialized.
    """
    if not request.state.conversation.security_analyzer:
        raise HTTPException(status_code=404, detail='Security analyzer not initialized')

    response = await request.state.conversation.security_analyzer.handle_api_request(
        request
    )
    if not isinstance(response, dict):
        raise HTTPException(status_code=500, detail='Invalid response from security analyzer')
    return response
