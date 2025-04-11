from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse

from openhands.core.logger import openhands_logger as logger

app = APIRouter(prefix='/api/conversations/{conversation_id}')


@app.get('/tools')
async def get_tools(request: Request) -> JSONResponse:
    """Get available tools for the agent.

    This function retrieves the current tools available to the agent and returns them.

    Args:
        request (Request): The incoming request object.

    Returns:
        JSONResponse: A JSON response containing the tools as a list.
    """
    try:
        # Get the agent_session from the conversation
        agent_session = request.state.conversation
        logger.debug(f"Agent session type: {type(agent_session)}")
        
        # Check if the agent_session has a controller attribute
        if hasattr(agent_session, 'controller') and agent_session.controller is not None:
            # Get the agent from the controller
            agent = agent_session.controller.agent
            logger.debug(f"Agent type: {type(agent)}")
            
            # Get the tools from the agent
            if hasattr(agent, 'get_tools'):
                tools = agent.get_tools()
                logger.debug(f"Tools from get_tools(): {tools}")
            elif hasattr(agent, 'mcp_tools'):
                tools = agent.mcp_tools
                logger.debug(f"Tools from mcp_tools: {tools}")
            else:
                tools = []
                logger.warning("Agent has no tools attribute")
        else:
            tools = []
            logger.warning("Agent session has no controller or controller is None")

        # Log the tools for debugging
        logger.debug(f"Returning tools: {tools}")
        return JSONResponse(status_code=status.HTTP_200_OK, content={'tools': tools})
    except Exception as e:
        logger.error(f'Error getting tools: {e}', exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                'tools': None,
                'error': f'Error getting tools: {e}',
            },
        )
