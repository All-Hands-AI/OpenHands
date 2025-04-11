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
        # Get the agent from the conversation state
        agent = request.state.conversation.agent_controller.agent

        # Get the tools from the agent
        tools = agent.mcp_tools

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
