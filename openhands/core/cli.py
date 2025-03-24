#!/usr/bin/env python3
import asyncio
import json
import logging
import os
import sys
import time
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import uvicorn
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from openhands.core.agent_session import AgentSession
from openhands.core.config import Config
from openhands.core.event_stream import EventStream
from openhands.core.memory import Memory, create_memory
from openhands.core.microagent import MicroAgent
from openhands.core.runtime import Runtime
from openhands.core.sandbox import (
    initialize_repository_for_runtime,
    initialize_sandbox_for_runtime,
)
from openhands.core.session_manager import SessionManager
from openhands.core.utils import (
    get_frontend_dir,
    get_frontend_dist_dir,
    get_frontend_index_path,
    get_frontend_port,
    get_frontend_url,
    get_host,
    get_port,
    get_use_tls,
)

logger = logging.getLogger(__name__)

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files from the frontend dist directory
frontend_dist_dir = get_frontend_dist_dir()
if os.path.exists(frontend_dist_dir):
    app.mount("/", StaticFiles(directory=frontend_dist_dir, html=True), name="static")


@app.get("/api/health")
async def health_check():
    return {"status": "ok"}


@app.get("/api/config")
async def get_config():
    config = Config.get_instance()
    return config.model_dump()


@app.post("/api/config")
async def update_config(request: Request):
    config = Config.get_instance()
    data = await request.json()
    for key, value in data.items():
        if hasattr(config, key):
            setattr(config, key, value)
    config.save()
    return config.model_dump()


@app.post("/api/reset_config")
async def reset_config():
    config = Config.get_instance()
    config.reset()
    return config.model_dump()


@app.get("/api/repositories")
async def get_repositories():
    config = Config.get_instance()
    return {"repositories": config.sandbox.repositories}


@app.post("/api/repositories")
async def add_repository(request: Request):
    config = Config.get_instance()
    data = await request.json()
    repo_url = data.get("url")
    if not repo_url:
        return JSONResponse(status_code=400, content={"error": "Repository URL is required"})

    # Check if repository already exists
    for repo in config.sandbox.repositories:
        if repo.url == repo_url:
            return JSONResponse(
                status_code=400, content={"error": "Repository already exists"}
            )

    # Add repository
    config.sandbox.add_repository(repo_url)
    config.save()
    return {"repositories": config.sandbox.repositories}


@app.delete("/api/repositories/{repo_id}")
async def delete_repository(repo_id: str):
    config = Config.get_instance()
    config.sandbox.remove_repository(repo_id)
    config.save()
    return {"repositories": config.sandbox.repositories}


@app.post("/api/repositories/{repo_id}/select")
async def select_repository(repo_id: str):
    config = Config.get_instance()
    config.sandbox.select_repository(repo_id)
    config.save()
    return {"selected_repo": config.sandbox.selected_repo}


@app.get("/api/repositories/{repo_id}/files")
async def get_repository_files(repo_id: str):
    config = Config.get_instance()
    repo = config.sandbox.get_repository(repo_id)
    if not repo:
        return JSONResponse(status_code=404, content={"error": "Repository not found"})

    # TODO: Implement file listing
    return {"files": []}


@app.get("/api/sessions")
async def get_sessions():
    session_manager = SessionManager.get_instance()
    return {"sessions": session_manager.get_sessions()}


@app.post("/api/sessions")
async def create_session(request: Request):
    data = await request.json()
    session_id = data.get("session_id")
    if not session_id:
        return JSONResponse(status_code=400, content={"error": "Session ID is required"})

    session_manager = SessionManager.get_instance()
    session = session_manager.create_session(session_id)
    return {"session": session}


@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    session_manager = SessionManager.get_instance()
    session_manager.delete_session(session_id)
    return {"success": True}


@app.websocket("/api/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    session_manager = SessionManager.get_instance()
    session = session_manager.get_session(session_id)
    if not session:
        session = session_manager.create_session(session_id)

    # Create event stream
    event_stream = EventStream()
    event_stream.add_websocket(websocket)

    # Create runtime
    config = Config.get_instance()
    runtime = Runtime(config=config, event_stream=event_stream)

    # Initialize sandbox if needed
    initialize_sandbox_for_runtime(runtime)

    # Initialize repository if needed
    repo_directory = None
    if config.sandbox.selected_repo:
        repo_directory = initialize_repository_for_runtime(
            runtime,
            selected_repository=config.sandbox.selected_repo,
        )
        
        # Run setup script if it exists
        runtime.maybe_run_setup_script()

    # when memory is created, it will load the microagents from the selected repository
    memory = create_memory(
        runtime=runtime,
        event_stream=event_stream,
        repo_directory=repo_directory,
    )

    # Create agent session
    agent_session = AgentSession(
        session_id=session_id,
        runtime=runtime,
        memory=memory,
        event_stream=event_stream,
    )

    try:
        # Start agent session
        await agent_session.start()

        # Process messages
        while True:
            try:
                message = await websocket.receive_text()
                data = json.loads(message)
                await agent_session.process_message(data)
            except WebSocketDisconnect:
                logger.info(f"Client disconnected: {session_id}")
                break
            except Exception as e:
                logger.exception(f"Error processing message: {e}")
                await event_stream.send_error(str(e))
    except Exception as e:
        logger.exception(f"Error in websocket endpoint: {e}")
    finally:
        # Stop agent session
        await agent_session.stop()
        event_stream.remove_websocket(websocket)


async def main(loop: asyncio.AbstractEventLoop):
    config = Config.get_instance()
    host = get_host()
    port = get_port()
    use_tls = get_use_tls()

    # Start uvicorn server
    config = uvicorn.Config(
        app=app,
        host=host,
        port=port,
        loop=loop,
        log_level="info",
        ssl_certfile=os.environ.get("SSL_CERTFILE") if use_tls else None,
        ssl_keyfile=os.environ.get("SSL_KEYFILE") if use_tls else None,
    )
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main(loop))
    except KeyboardInterrupt:
        print('Received keyboard interrupt, shutting down...')
    except ConnectionRefusedError as e:
        print(f'Connection refused: {e}')
        sys.exit(1)
    except Exception as e:
        print(f'An error occurred: {e}')
        sys.exit(1)
    finally:
        try:
            # Cancel all running tasks
            pending = asyncio.all_tasks(loop)
            for task in pending:
                task.cancel()
            # Wait for all tasks to complete with a timeout
            loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            loop.close()
        except Exception as e:
            print(f'Error during cleanup: {e}')
            sys.exit(1)
