from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from openhands.core.logger import openhands_logger as logger
from openhands.runtime.base import Runtime

app = APIRouter(prefix='/api/conversations/{conversation_id}')


@app.get('/config')
async def get_remote_runtime_config(request: Request):
    """Retrieve the runtime configuration.

    Currently, this is the session ID and runtime ID (if available).
    """
    runtime = request.state.conversation.runtime
    runtime_id = runtime.runtime_id if hasattr(runtime, 'runtime_id') else None
    session_id = runtime.sid if hasattr(runtime, 'sid') else None
    return JSONResponse(
        content={
            'runtime_id': runtime_id,
            'session_id': session_id,
        }
    )


class ConversationMetrics(BaseModel):
    """Model for conversation metrics."""

    model: str
    total_cost: float
    total_input_tokens: int
    total_output_tokens: int
    total_cache_hit_tokens: int


@app.get('/metrics', response_model=ConversationMetrics)
async def get_conversation_metrics(request: Request):
    """Get metrics for the current conversation.

    Returns:
        JSONResponse: A JSON response containing:
            - model: The LLM model being used
            - total_cost: The total cost for the conversation so far
            - total_input_tokens: The total number of input tokens used
            - total_output_tokens: The total number of output tokens used
            - total_cache_hit_tokens: The total number of cache hit tokens
    """
    try:
        # Get the agent controller from the conversation
        controller = request.state.conversation.runtime.agent_session.controller
        if not controller or not controller.agent or not controller.agent.llm:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={'error': 'LLM not found for this conversation'},
            )

        # Get the metrics from the LLM
        llm = controller.agent.llm
        metrics = llm.metrics

        # Get the accumulated token usage
        token_usage = metrics._accumulated_token_usage

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                'model': metrics.model_name,
                'total_cost': metrics.accumulated_cost,
                'total_input_tokens': token_usage.prompt_tokens,
                'total_output_tokens': token_usage.completion_tokens,
                'total_cache_hit_tokens': token_usage.cache_read_tokens,
            },
        )
    except Exception as e:
        logger.error(f'Error getting conversation metrics: {e}')
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={'error': f'Error getting conversation metrics: {e}'},
        )


@app.get('/vscode-url')
async def get_vscode_url(request: Request):
    """Get the VSCode URL.

    This endpoint allows getting the VSCode URL.

    Args:
        request (Request): The incoming FastAPI request object.

    Returns:
        JSONResponse: A JSON response indicating the success of the operation.
    """
    try:
        runtime: Runtime = request.state.conversation.runtime
        logger.debug(f'Runtime type: {type(runtime)}')
        logger.debug(f'Runtime VSCode URL: {runtime.vscode_url}')
        return JSONResponse(
            status_code=status.HTTP_200_OK, content={'vscode_url': runtime.vscode_url}
        )
    except Exception as e:
        logger.error(f'Error getting VSCode URL: {e}')
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                'vscode_url': None,
                'error': f'Error getting VSCode URL: {e}',
            },
        )


@app.get('/web-hosts')
async def get_hosts(request: Request):
    """Get the hosts used by the runtime.

    This endpoint allows getting the hosts used by the runtime.

    Args:
        request (Request): The incoming FastAPI request object.

    Returns:
        JSONResponse: A JSON response indicating the success of the operation.
    """
    try:
        if not hasattr(request.state, 'conversation'):
            return JSONResponse(
                status_code=500,
                content={'error': 'No conversation found in request state'},
            )

        if not hasattr(request.state.conversation, 'runtime'):
            return JSONResponse(
                status_code=500, content={'error': 'No runtime found in conversation'}
            )

        runtime: Runtime = request.state.conversation.runtime
        logger.debug(f'Runtime type: {type(runtime)}')
        logger.debug(f'Runtime hosts: {runtime.web_hosts}')
        return JSONResponse(status_code=200, content={'hosts': runtime.web_hosts})
    except Exception as e:
        logger.error(f'Error getting runtime hosts: {e}')
        return JSONResponse(
            status_code=500,
            content={
                'hosts': None,
                'error': f'Error getting runtime hosts: {e}',
            },
        )
