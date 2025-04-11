from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse

from openhands.core.logger import openhands_logger as logger
from openhands.events.async_event_store_wrapper import AsyncEventStoreWrapper
from openhands.server.session.agent_session import AgentSession

app = APIRouter(prefix='/api/conversations/{conversation_id}')


@app.get('/tools')
async def get_tools(request: Request) -> JSONResponse:
    """Get available tools for the agent.

    This function retrieves the current tools available to the agent and returns them.
    It first tries to get tools from the event stream, and if not found, falls back to
    getting them directly from the agent.

    Args:
        request (Request): The incoming request object.

    Returns:
        JSONResponse: A JSON response containing the tools as a list.
    """
    try:
        # Get the agent_session from the conversation
        agent_session = request.state.conversation
        logger.debug(f"Agent session type: {type(agent_session)}")
        
        # Log detailed information about the agent_session structure
        logger.debug(f"Agent session attributes: {dir(agent_session)}")
        
        # Check for controller and event_stream
        has_controller = hasattr(agent_session, 'controller')
        has_event_stream = hasattr(agent_session, 'event_stream')
        logger.debug(f"Has controller: {has_controller}, Has event_stream: {has_event_stream}")
        
        # If controller exists, log its attributes
        if has_controller and agent_session.controller is not None:
            logger.debug(f"Controller attributes: {dir(agent_session.controller)}")
            
            # Check if controller has agent
            has_agent = hasattr(agent_session.controller, 'agent')
            logger.debug(f"Controller has agent: {has_agent}")
            
            if has_agent and agent_session.controller.agent is not None:
                logger.debug(f"Agent attributes: {dir(agent_session.controller.agent)}")
                logger.debug(f"Agent has mcp_tools: {hasattr(agent_session.controller.agent, 'mcp_tools')}")
                logger.debug(f"Agent has get_tools: {hasattr(agent_session.controller.agent, 'get_tools')}")
        
        # First approach: Try to get tools from the agent directly
        tools = await get_tools_from_agent(agent_session)
        
        # If no tools found from agent, try to get from event stream
        if not tools:
            logger.debug("No tools found from agent, trying event stream...")
            tools = await get_tools_from_event_stream(agent_session)
            
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


async def get_tools_from_agent(agent_session) -> list[dict]:
    """Get tools directly from the agent object.
    
    Args:
        agent_session: The agent session object.
        
    Returns:
        list[dict]: The list of tools.
    """
    # Verify we have an AgentSession
    if not isinstance(agent_session, AgentSession):
        logger.warning(f"Expected AgentSession but got {type(agent_session)}")
        return []
    
    # Check if the agent_session has a controller attribute
    if agent_session.controller is None:
        logger.warning("Agent session controller is None")
        return []
        
    # Get the agent from the controller
    agent = agent_session.controller.agent
    if agent is None:
        logger.warning("Agent is None")
        return []
        
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
        
    return tools


async def get_tools_from_event_stream(agent_session) -> list[dict]:
    """Get tools from the event stream.
    
    This function looks for tools in the event stream by examining MessageAction events
    that might contain tool information.
    
    Args:
        agent_session: The agent session object.
        
    Returns:
        list[dict]: The list of tools.
    """
    if not hasattr(agent_session, 'event_stream'):
        logger.warning("Agent session has no event_stream attribute")
        return []
        
    try:
        # Create an async wrapper for the event stream
        async_store = AsyncEventStoreWrapper(agent_session.event_stream, filter_hidden=False)
        
        # Look for tools in the event stream
        tools = []
        async for event in async_store:
            # Check if this is a MessageAction with tools information
            if hasattr(event, 'action') and event.action == 'message':
                # Look for tools in the message content
                if hasattr(event, 'content') and 'tools' in event.content.lower():
                    logger.debug(f"Found potential tools message: {event.content[:100]}...")
                    
            # If the agent has tools attribute, check if it was set in this event
            if hasattr(event, 'agent') and hasattr(event.agent, 'mcp_tools'):
                tools = event.agent.mcp_tools
                logger.debug(f"Found tools in event: {tools}")
                break
                
        return tools
    except Exception as e:
        logger.error(f"Error getting tools from event stream: {e}", exc_info=True)
        return []
