from fastapi import (
    APIRouter,
    HTTPException,
    Request,
    Response,
    status,
)

app = APIRouter(prefix='/api/conversations/{conversation_id}')


@app.route('/security/{path:path}', methods=['GET', 'POST', 'PUT', 'DELETE'])
async def security_api(request: Request) -> Response:
    """Catch-all route for security analyzer API requests.

    Each request is handled directly to the security analyzer.

    Args:
        request (Request): The incoming FastAPI request object.

    Returns:
        Response: The response from the security analyzer.

    Raises:
        HTTPException: If the security analyzer is not initialized.
    """
    if not request.state.conversation.security_analyzer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Security analyzer not initialized',
        )

    return await request.state.conversation.security_analyzer.handle_api_request(
        request
    )
