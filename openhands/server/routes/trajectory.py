from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse

from openhands.core.logger import openhands_logger as logger
from openhands.events.async_event_store_wrapper import AsyncEventStoreWrapper
from openhands.events.serialization import event_to_trajectory
from openhands.memory.trajectory_summarizer.summarizer import TrajectorySummarizer
from openhands.server.shared import conversation_manager

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
        # Get the session ID from the conversation
        sid = request.state.conversation.sid
        logger.info(f'DEBUG - Getting trajectory summary for conversation {sid}')

        # Get the agent session from the conversation manager
        session = conversation_manager._local_agent_loops_by_sid.get(sid)
        if not session:
            logger.error(f'DEBUG - No active session found for conversation {sid}')
            raise ValueError(f'No active session found for conversation {sid}')

        agent_session = session.agent_session
        if not agent_session or not agent_session.controller:
            logger.error(f'DEBUG - No agent controller found for conversation {sid}')
            raise ValueError(f'No agent controller found for conversation {sid}')

        # Get the LLM from the agent controller
        llm = agent_session.controller.agent.llm
        logger.info(f'DEBUG - Using LLM: {llm.__class__.__name__}')

        # Create a summarizer using the same LLM
        summarizer = TrajectorySummarizer(llm=llm)
        logger.info(f'DEBUG - Created summarizer: {summarizer.__class__.__name__}')

        # Get the event stream from the conversation
        event_stream = request.state.conversation.event_stream
        # logger.info(f"DEBUG - Got event stream with {len(event_stream.events)} events")

        # Summarize the conversation
        logger.info('DEBUG - Starting conversation summarization')
        summary = await summarizer.summarize_conversation(event_stream)
        logger.info(
            f"DEBUG - Summarization complete with {len(summary.get('segments', []))} segments"
        )

        # Log the summary structure
        logger.info(
            f"DEBUG - Summary structure: overall_summary and {len(summary.get('segments', []))} segments"
        )
        
        # Ensure segments exist
        if 'segments' not in summary or not isinstance(summary['segments'], list):
            logger.warning("No segments found in summary, creating empty segments array")
            summary['segments'] = []
            
        # Ensure each segment has an ids array
        for i, segment in enumerate(summary.get('segments', [])):
            if 'ids' not in segment or not isinstance(segment['ids'], list):
                logger.warning(f"Segment {i} has no ids array, creating empty ids array")
                segment['ids'] = []
                
            # Log segment details
            logger.info(
                f"DEBUG - Segment {i}: {segment.get('title')} with {len(segment.get('ids', []))} IDs"
            )
            logger.info(f"DEBUG - Segment {i} IDs: {segment.get('ids', [])}")
            
            # Ensure all IDs are integers
            processed_ids = []
            for id_val in segment.get('ids', []):
                try:
                    if isinstance(id_val, str) and id_val.isdigit():
                        processed_ids.append(int(id_val))
                    elif isinstance(id_val, (int, float)):
                        processed_ids.append(int(id_val))
                except (ValueError, TypeError):
                    logger.warning(f'Could not convert ID {id_val} to integer')
            
            segment['ids'] = processed_ids
            logger.info(f"DEBUG - Processed Segment {i} IDs: {segment['ids']}")

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
