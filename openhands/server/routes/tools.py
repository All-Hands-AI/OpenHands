from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse

from openhands.core.logger import openhands_logger as logger
from openhands.server.session.agent_session import AgentSession

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
        
        # Verify we have an AgentSession
        if not isinstance(agent_session, AgentSession):
            logger.warning(f"Expected AgentSession but got {type(agent_session)}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    'tools': [],
                    'error': f'Invalid session type: {type(agent_session)}',
                },
            )
        
        # Check if the agent_session has a controller attribute
        if agent_session.controller is None:
            logger.warning("Agent session controller is None")
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={'tools': []},
            )
            
        # Get the agent from the controller
        agent = agent_session.controller.agent
        if agent is None:
            logger.warning("Agent is None")
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={'tools': []},
            )
            
        logger.debug(f"Agent type: {type(agent)}")
        
        # Get the tools from the agent
        tools = []
        if hasattr(agent, 'get_tools') and callable(getattr(agent, 'get_tools')):
            try:
                tools = agent.get_tools()
                logger.debug(f"Tools from get_tools(): {tools}")
            except Exception as e:
                logger.error(f"Error calling get_tools(): {e}", exc_info=True)
        elif hasattr(agent, 'mcp_tools'):
            try:
                tools = agent.mcp_tools
                logger.debug(f"Tools from mcp_tools attribute: {tools}")
            except Exception as e:
                logger.error(f"Error accessing mcp_tools: {e}", exc_info=True)
        else:
            logger.warning("Agent has no tools attribute or get_tools method")

        # Log the tools for debugging
        logger.debug(f"Returning tools: {tools}")
        return JSONResponse(status_code=status.HTTP_200_OK, content={'tools': tools or []})
    except Exception as e:
        logger.error(f'Error getting tools: {e}', exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                'tools': [],
                'error': f'Error getting tools: {e}',
            },
        )
