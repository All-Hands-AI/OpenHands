from typing import Annotated, cast

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    Response,
    status,
)
from fastapi.routing import APIRoute

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


def get_route() -> APIRoute:
    """Get the route for the security API.

    Returns:
        APIRoute: The route for the security API.
    """
    return cast(
        APIRoute,
        app.api_route(
            '/security/{path:path}',
            methods=['GET', 'POST', 'PUT', 'DELETE'],
            response_model=None,
        ),
    )


async def security_api(
    response: Annotated[Response, Depends(get_response)],
) -> Response:
    """Catch-all route for security analyzer API requests.

    Args:
        response (Response): The response from the security analyzer.

    Returns:
        Response: The response from the security analyzer.
    """
    return response


route = get_route()
route.endpoint = security_api
