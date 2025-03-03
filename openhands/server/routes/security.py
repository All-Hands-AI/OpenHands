from fastapi import (
    APIRouter,
    HTTPException,
    Request,
    Response,
    status,
)

app = APIRouter(prefix='/api/conversations/{conversation_id}')


async def get_response(request: Request) -> Response:
    """Get response from security analyzer.

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
