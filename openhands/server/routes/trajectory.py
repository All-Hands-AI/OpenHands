from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse

from openhands.core.logger import openhands_logger as logger
from openhands.events.async_event_store_wrapper import AsyncEventStoreWrapper
from openhands.events.serialization import event_to_trajectory
from openhands.llm.llm import LLM
from openhands.memory.condenser.impl.llm_summarizing_condenser import (
    LLMSummarizingCondenser,
)
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

        # Get the LLM from the agent controller
        from openhands.server.agent_controller import get_agent_controller

        # Get the agent controller
        agent_controller = get_agent_controller()

        # Use the agent controller's LLM directly
        if (
            agent_controller
            and hasattr(agent_controller, 'agent')
            and agent_controller.agent
            and hasattr(agent_controller.agent, 'llm')
            and agent_controller.agent.llm
        ):
            llm = agent_controller.agent.llm
        else:
            # Try to get the LLM from the conversation's controller
            controller = getattr(request.state.conversation, 'controller', None)
            if (
                controller
                and hasattr(controller, 'agent')
                and controller.agent
                and hasattr(controller.agent, 'llm')
                and controller.agent.llm
            ):
                llm = controller.agent.llm
            else:
                # Fallback to creating a new LLM with default config if agent controller's LLM is not available
                from openhands.config.llm import LLMConfig

                llm_config = LLMConfig()
                llm = LLM(config=llm_config)

        # Create the condenser with the LLM
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
            content={'summary': condensation.action.summary},
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
