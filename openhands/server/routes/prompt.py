from typing import Annotated, Optional
from fastapi import APIRouter, Query, Request
from pydantic import BaseModel
from openhands.server.thesis_auth import handle_thesis_auth_request


app = APIRouter(prefix='/api/prompts', tags=["Prompts"])


class SavePromptRequest(BaseModel):
    content: str
    conversationId: Optional[str] = None


class GetPromptsQuery(BaseModel):
    conversationId: Optional[str] = None
    page: Optional[int] = 1
    limit: Optional[int] = 20
    keyword: Optional[str] = None


class RemoveBatchRequest(BaseModel):
    ids: list[int]


@app.post('')
async def save_prompt(request: Request, data: SavePromptRequest):
    """Save a interested prompt"""
    bearer_token = request.headers.get('Authorization')
    return await handle_thesis_auth_request('POST', '/api/prompts', bearer_token, data.model_dump())


@app.get('')
async def get_prompts(request: Request, filter_query: Annotated[GetPromptsQuery, Query()]):
    """Get all prompts"""
    bearer_token = request.headers.get('Authorization')
    return await handle_thesis_auth_request('GET', '/api/prompts', bearer_token, params=filter_query.model_dump())


@app.delete('/{prompt_id}')
async def delete_prompt(request: Request, prompt_id: str):
    bearer_token = request.headers.get('Authorization')
    return await handle_thesis_auth_request('DELETE', f'/api/prompts/{prompt_id}', bearer_token)


@app.post('/remove-batch')
async def remove_batch(request: Request, data: RemoveBatchRequest):
    bearer_token = request.headers.get('Authorization')
    return await handle_thesis_auth_request('POST', '/api/prompts/remove-ids', bearer_token, data.model_dump())
