from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from openhands.server.routes.instructions import (
    add_permanent_microagent,
    add_temporary_microagent,
    create_instructions_pr,
    get_repo_instructions,
    get_repo_microagents,
)

app = APIRouter()


class CreateInstructionsRequest(BaseModel):
    repo: str
    instructions: str


class AddMicroagentRequest(BaseModel):
    repo: str
    instructions: str


@app.get('/api/instructions')
async def get_instructions(repo: str):
    try:
        return get_repo_instructions(repo)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post('/api/instructions/create')
async def create_instructions(request: CreateInstructionsRequest):
    try:
        return create_instructions_pr(request.repo, request.instructions)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/api/microagents')
async def get_microagents(repo: str):
    try:
        return get_repo_microagents(repo)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post('/api/microagents/temporary')
async def add_temporary(request: AddMicroagentRequest):
    try:
        return add_temporary_microagent(request.repo, request.instructions)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post('/api/microagents/permanent')
async def add_permanent(request: AddMicroagentRequest):
    try:
        return add_permanent_microagent(request.repo, request.instructions)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
