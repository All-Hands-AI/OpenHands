from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from openhands.core.logger import openhands_logger as logger
from openhands.events.serialization import event_to_trajectory
from openhands.events.stream import AsyncEventStreamWrapper

app = APIRouter(prefix='/api/conversations/{conversation_id}')


@app.get('/trajectory')
async def get_trajectory(request: Request):
    """Get trajectory.

    This function retrieves the current trajectory and returns it.

    Args:
        request (Request): The incoming request object.

    Returns:
        JSONResponse: A JSON response containing the trajectory as a list of
        events.
    """
    try:
        async_stream = AsyncEventStreamWrapper(
            request.state.conversation.event_stream, filter_hidden=True
        )
        trajectory = []
        async for event in async_stream:
            trajectory.append(event_to_trajectory(event))
        return JSONResponse(status_code=200, content={'trajectory': trajectory})
    except Exception as e:
        logger.error(f'Error getting trajectory: {e}', exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                'trajectory': None,
                'error': f'Error getting trajectory: {e}',
            },
        )
