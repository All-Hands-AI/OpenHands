import os
import uuid
from datetime import datetime, timedelta, timezone

from opendevin.server.session import Session
from opendevin.agent import Agent
import agenthub  # noqa F401 (we import this to get the agents registered)

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import litellm
import jwt
from starlette import status
from starlette.responses import JSONResponse

JWT_SECRET = os.getenv("JWT_SECRET", "5ecRe7")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# This endpoint receives events from the client (i.e. the browser)
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    session = Session(websocket)
    # TODO: should this use asyncio instead of await?
    await session.start_listening()


@app.get("/litellm-models")
async def get_litellm_models():
    """
    Get all models supported by LiteLLM.
    """
    return litellm.model_list


@app.get("/litellm-agents")
async def get_litellm_agents():
    """
    Get all agents supported by LiteLLM.
    """
    return Agent.listAgents()


@app.get("/auth")
async def get_token():
    """
    Get token for authentication when starts a websocket connection.
    """
    payload = {
        "sid": str(uuid.uuid4()),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
    }
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"token": jwt.encode(payload, JWT_SECRET, algorithm="HS256")},
    )
