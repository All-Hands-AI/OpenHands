import os
import uuid

from opendevin.server.session import session_manager, message_stack
from opendevin.server.auth import get_sid_from_token, sign_token
from opendevin.agent import Agent
from opendevin.server.agent import AgentManager
import agenthub  # noqa F401 (we import this to get the agents registered)

from fastapi import FastAPI, WebSocket, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import litellm
from starlette import status
from starlette.responses import JSONResponse
from opendevin import config

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security_scheme = HTTPBearer()


# This endpoint receives events from the client (i.e. the browser)
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    sid = get_sid_from_token(websocket.query_params.get("token") or "")
    if sid == "":
        return
    session_manager.add_session(sid, websocket)
    # TODO: actually the agent_manager is created for each websocket connection, even if the session id is the same,
    # we need to manage the agent in memory for reconnecting the same session id to the same agent
    agent_manager = AgentManager(sid)
    await session_manager.loop_recv(sid, agent_manager.dispatch)


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
async def get_token(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
):
    """
    Get token for authentication when starts a websocket connection.
    """
    sid = get_sid_from_token(credentials.credentials) or str(uuid.uuid4())
    token = sign_token({"sid": sid})
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"token": token},
    )


@app.get("/messages")
async def get_messages(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
):
    data = []
    sid = get_sid_from_token(credentials.credentials)
    if sid != "":
        data = message_stack.get_messages(sid)

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"messages": data},
    )


@app.get("/messages/total")
async def get_message_total(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
):
    sid = get_sid_from_token(credentials.credentials)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"msg_total": message_stack.get_message_total(sid)},
    )


@app.delete("/messages")
async def del_messages(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
):
    sid = get_sid_from_token(credentials.credentials)
    message_stack.del_messages(sid)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"ok": True},
    )


@app.get("/default-model")
def read_default_model():
    return config.get_or_error("LLM_MODEL")
