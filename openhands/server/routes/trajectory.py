from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse

from openhands.core.config.condenser_config import LLMSummarizingCondenserConfig
from openhands.core.logger import openhands_logger as logger
from openhands.events.async_event_store_wrapper import AsyncEventStoreWrapper
from openhands.events.serialization import event_to_trajectory
from openhands.llm.llm import LLM
from openhands.memory.condenser.impl.llm_summarizing_condenser import LLMSummarizingCondenser
from openhands.memory.view import View

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


@app.get('/summarize')
async def summarize_conversation(request: Request) -> JSONResponse:
    """Summarize conversation.

    This function retrieves the current conversation and summarizes it using the
    LLMSummarizingCondenser.

    Args:
        request (Request): The incoming request object.

    Returns:
        JSONResponse: A JSON response containing the summary as a string.
    """
    try:
        # Get the conversation events
        async_store = AsyncEventStoreWrapper(
            request.state.conversation.event_stream, filter_hidden=True
        )
        events = []
        async for event in async_store:
            events.append(event)

        # Create a view from the events
        view = View.from_events(events)

        # Get the LLM configuration from the agent
        controller = request.state.conversation.controller
        if controller and controller.agent and controller.agent.llm:
            llm_config = controller.agent.llm.config
        else:
            # Use default LLM config if agent is not available
            llm_config = request.state.conversation.config.get_llm_config()

        # Create the condenser
        condenser_config = LLMSummarizingCondenserConfig(
            llm_config=llm_config, keep_first=3, max_size=40
        )
        llm = LLM(config=llm_config)
        condenser = LLMSummarizingCondenser(llm=llm, max_size=40, keep_first=3)

        # Force summarization by setting a large max_size
        original_max_size = condenser.max_size
        condenser.max_size = 0  # This ensures should_condense() returns True
        
        # Get the condensation
        condensation = condenser.get_condensation(view)
        
        # Restore the original max_size
        condenser.max_size = original_max_size

        # Return the summary
        return JSONResponse(
            status_code=status.HTTP_200_OK, 
            content={'summary': condensation.action.summary}
        )
    except Exception as e:
        logger.error(f'Error summarizing conversation: {e}', exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                'summary': None,
                'error': f'Error summarizing conversation: {e}',
            },
        )
