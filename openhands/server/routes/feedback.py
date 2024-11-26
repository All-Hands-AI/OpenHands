from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from openhands.core.logger import openhands_logger as logger
from openhands.events.serialization import event_to_dict
from openhands.events.stream import AsyncEventStreamWrapper
from openhands.server.data_models.feedback import FeedbackDataModel, store_feedback
from openhands.server.shared import config
from openhands.utils.async_utils import call_sync_from_async

app = APIRouter(prefix='/api')


@app.post('/submit-feedback')
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
