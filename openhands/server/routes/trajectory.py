from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse

from openhands.core.logger import openhands_logger as logger
from openhands.events.async_event_store_wrapper import AsyncEventStoreWrapper
from openhands.events.serialization import event_to_trajectory
from openhands.memory.trajectory_summarizer.summarizer import TrajectorySummarizer

app = APIRouter(prefix='/api/conversations/{conversation_id}')


@app.get('/trajectory')
async def get_trajectory(request: Request) -> JSONResponse:
    """Get trajectory.

    This function retrieves the current trajectory and returns it.

    Args:
        request (Request): The incoming request object.

    Returns:
        JSONResponse: A JSON response containing the trajectory as a list of
        events.
    """
    try:
        async_store = AsyncEventStoreWrapper(
            request.state.conversation.event_stream, filter_hidden=True
        )
        trajectory = []
        async for event in async_store:
            trajectory.append(event_to_trajectory(event))
        return JSONResponse(
            status_code=status.HTTP_200_OK, content={'trajectory': trajectory}
        )
    except Exception as e:
        logger.error(f'Error getting trajectory: {e}', exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                'trajectory': None,
                'error': f'Error getting trajectory: {e}',
            },
        )


@app.get('/summary')
async def get_trajectory_summary(request: Request) -> JSONResponse:
    """Get a summary of the trajectory.

    This function summarizes the current trajectory and returns a structured summary.

    Args:
        request (Request): The incoming request object.

    Returns:
        JSONResponse: A JSON response containing the summary with overall summary and segments.
    """
    try:
        # Get the LLM from the conversation's agent
        llm = request.state.conversation.agent.llm

        # Create a summarizer using the same LLM
        summarizer = TrajectorySummarizer(llm=llm)

        # Get the event stream from the conversation
        event_stream = request.state.conversation.event_stream

        # Summarize the conversation
        summary = await summarizer.summarize_conversation(event_stream)

        return JSONResponse(status_code=status.HTTP_200_OK, content=summary)
    except Exception as e:
        logger.error(f'Error summarizing trajectory: {e}', exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                'overall_summary': f'Error summarizing trajectory: {e}',
                'segments': [],
                'error': str(e),
            },
        )
