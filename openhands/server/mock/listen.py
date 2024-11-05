import asyncio
import sys
import time
from typing import Callable

import uvicorn
from fastapi import FastAPI, HTTPException, Request, WebSocket
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from openhands.core.logger import openhands_logger as logger
from openhands.core.schema import ActionType
from openhands.runtime.utils.shutdown_listener import should_continue


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for consistent error handling across all endpoints.
    
    This middleware catches unhandled exceptions and converts them to
    appropriate HTTP responses with proper error messages and logging.
    """
    
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> JSONResponse:
        """Process a request and handle any errors.
        
        Args:
            request: The incoming request
            call_next: The next middleware or endpoint to call
            
        Returns:
            JSONResponse: The response with appropriate error handling
        """
        try:
            # Add request ID for tracking
            request.state.request_id = id(request)
            logger.debug(
                f'Processing request {request.state.request_id}: '
                f'{request.method} {request.url.path}'
            )
            
            # Process request
            response = await call_next(request)
            return response
            
        except HTTPException as e:
            # Handle known HTTP errors
            logger.warning(
                f'HTTP error {e.status_code} on request {request.state.request_id}: '
                f'{e.detail}'
            )
            return JSONResponse(
                status_code=e.status_code,
                content={'error': e.detail}
            )
            
        except Exception as e:
            # Handle unexpected errors
            logger.error(
                f'Unexpected error on request {request.state.request_id}: {str(e)}',
                exc_info=True
            )
            return JSONResponse(
                status_code=500,
                content={'error': 'Internal server error'}
            )


# Initialize FastAPI app with error handling
app = FastAPI(title='OpenHands Mock Server')
app.add_middleware(ErrorHandlingMiddleware)


@app.websocket('/ws')
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for mock server.
    
    This endpoint simulates a basic server that:
    1. Accepts WebSocket connections
    2. Sends an initial message
    3. Echoes received messages back with a wrapper
    4. Handles various error conditions gracefully
    
    Args:
        websocket: The WebSocket connection
        
    Notes:
        - Invalid JSON messages are reported but don't close the connection
        - WebSocket state errors cause the connection to close
        - Unexpected errors are logged but don't crash the server
    """
    connection_id = id(websocket)
    logger.info(f'New WebSocket connection: {connection_id}')
    
    try:
        # Accept connection with timeout
        try:
            await asyncio.wait_for(websocket.accept(), timeout=5.0)
            logger.debug(f'Accepted connection: {connection_id}')
        except asyncio.TimeoutError:
            logger.error(f'Connection accept timeout: {connection_id}')
            return
        except Exception as e:
            logger.error(f'Error accepting connection: {str(e)}')
            return
            
        # Send initial message
        try:
            await websocket.send_json({
                'action': ActionType.INIT,
                'message': 'Control loop started.',
                'connection_id': connection_id
            })
            logger.debug(f'Sent initial message: {connection_id}')
        except Exception as e:
            logger.error(f'Error sending initial message: {str(e)}')
            return
            
        # Main message loop
        while should_continue():
            try:
                # Receive message with timeout
                try:
                    data = await asyncio.wait_for(
                        websocket.receive_json(),
                        timeout=60.0  # 1 minute timeout
                    )
                except asyncio.TimeoutError:
                    logger.warning(f'Message receive timeout: {connection_id}')
                    await websocket.send_json({
                        'error': True,
                        'message': 'Connection timed out'
                    })
                    break
                except ValueError as e:
                    logger.warning(f'Invalid JSON received on {connection_id}: {str(e)}')
                    await websocket.send_json({
                        'error': True,
                        'message': 'Invalid JSON format'
                    })
                    continue
                    
                # Log received message
                logger.debug(f'Received on {connection_id}: {data}')
                
                # Validate message format
                if not isinstance(data, dict):
                    logger.warning(f'Invalid message format on {connection_id}')
                    await websocket.send_json({
                        'error': True,
                        'message': 'Message must be a JSON object'
                    })
                    continue
                    
                # Send response
                try:
                    response = {
                        'message': f'receive {data}',
                        'timestamp': time.time(),
                        'connection_id': connection_id
                    }
                    await websocket.send_json(response)
                    logger.debug(f'Sent on {connection_id}: {response}')
                except Exception as e:
                    logger.error(f'Error sending response on {connection_id}: {str(e)}')
                    break
                    
            except WebSocketDisconnect:
                logger.info(f'Client disconnected: {connection_id}')
                break
            except RuntimeError as e:
                logger.error(f'WebSocket state error on {connection_id}: {str(e)}')
                break
            except Exception as e:
                logger.error(
                    f'Unexpected error on {connection_id}: {str(e)}',
                    exc_info=True
                )
                try:
                    await websocket.send_json({
                        'error': True,
                        'message': 'Internal server error'
                    })
                except Exception:
                    pass  # Ignore errors in error handling
                break
                
    except Exception as e:
        logger.error(
            f'Fatal error on connection {connection_id}: {str(e)}',
            exc_info=True
        )
        
    finally:
        # Ensure connection is closed
        try:
            await websocket.close()
            logger.info(f'Closed connection: {connection_id}')
        except Exception as e:
            logger.error(f'Error closing connection {connection_id}: {str(e)}')


@app.get('/')
async def read_root():
    """Root endpoint that confirms server is running.
    
    Returns:
        dict: A simple message indicating server status
        
    Raises:
        HTTPException: If there's an error generating the response
    """
    try:
        return {
            'message': 'This is a mock server',
            'status': 'running',
            'timestamp': time.time()
        }
    except Exception as e:
        logger.error(f'Error in root endpoint: {str(e)}')
        raise HTTPException(
            status_code=500,
            detail='Internal server error'
        )


@app.get('/api/options/models')
async def read_llm_models():
    """Get list of supported LLM models.
    
    Returns:
        list: Available LLM models
        
    Raises:
        HTTPException: If there's an error generating the model list
    """
    try:
        models = [
            'gpt-4',
            'gpt-4-turbo-preview',
            'gpt-4-0314',
            'gpt-4-0613',
        ]
        logger.debug(f'Returning {len(models)} models')
        return models
    except Exception as e:
        logger.error(f'Error getting model list: {str(e)}')
        raise HTTPException(
            status_code=500,
            detail='Failed to retrieve model list'
        )


@app.get('/api/options/agents')
async def read_llm_agents():
    """Get list of supported agent types.
    
    Returns:
        list: Available agent types
        
    Raises:
        HTTPException: If there's an error generating the agent list
    """
    try:
        agents = [
            'CodeActAgent',
            'PlannerAgent',
        ]
        logger.debug(f'Returning {len(agents)} agents')
        return agents
    except Exception as e:
        logger.error(f'Error getting agent list: {str(e)}')
        raise HTTPException(
            status_code=500,
            detail='Failed to retrieve agent list'
        )


@app.get('/api/list-files')
async def refresh_files():
    """Get list of files in the workspace.
    
    Returns:
        list: Available files
        
    Raises:
        HTTPException: If there's an error listing files
    """
    try:
        files = ['hello_world.py']
        logger.debug(f'Returning {len(files)} files')
        return files
    except Exception as e:
        logger.error(f'Error listing files: {str(e)}')
        raise HTTPException(
            status_code=500,
            detail='Failed to list files'
        )


if __name__ == '__main__':
    try:
        logger.info('Starting mock server on http://127.0.0.1:3000')
        uvicorn.run(
            app,
            host='127.0.0.1',
            port=3000,
            log_level='info'
        )
    except Exception as e:
        logger.error(f'Failed to start server: {str(e)}', exc_info=True)
        sys.exit(1)
