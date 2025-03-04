from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse

from openhands.core.logger import openhands_logger as logger
from openhands.runtime.base import Runtime

app = APIRouter(prefix='/api/conversations/{conversation_id}')


@app.get('/metrics')
async def get_conversation_metrics(request: Request):
    """Retrieve the conversation metrics.

    This endpoint returns the accumulated cost and token usage metrics for the conversation.
    Metrics are retrieved directly from the runtime's state rather than reconstructing from events,
    providing a more accurate representation of costs, including those not associated with events.

    Args:
        request (Request): The incoming FastAPI request object.

    Returns:
        JSONResponse: A JSON response containing the metrics data.
    """
    try:
        if not hasattr(request.state, 'conversation'):
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={'error': 'No conversation found in request state'},
            )

        conversation = request.state.conversation

        # Get metrics directly from the conversation's runtime state
        metrics = conversation.get_metrics()

        # If no metrics from state, fall back to event stream metrics for backward compatibility
        if not metrics and hasattr(conversation.event_stream, 'get_metrics'):
            metrics = conversation.event_stream.get_metrics()

        if not metrics:
            # Return empty metrics if not available
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    'accumulated_cost': 0.0,
                    'total_prompt_tokens': 0,
                    'total_completion_tokens': 0,
                    'total_tokens': 0,
                },
            )

        # Calculate total tokens
        total_prompt_tokens = sum(usage.prompt_tokens for usage in metrics.token_usages)
        total_completion_tokens = sum(
            usage.completion_tokens for usage in metrics.token_usages
        )
        total_tokens = total_prompt_tokens + total_completion_tokens

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                'accumulated_cost': metrics.accumulated_cost,
                'total_prompt_tokens': total_prompt_tokens,
                'total_completion_tokens': total_completion_tokens,
                'total_tokens': total_tokens,
            },
        )
    except Exception as e:
        logger.error(f'Error getting conversation metrics: {e}')
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                'error': f'Error getting conversation metrics: {e}',
            },
        )


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
