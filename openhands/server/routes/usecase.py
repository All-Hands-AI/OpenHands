from typing import Annotated

from fastapi import APIRouter, Query, Request
from pydantic import BaseModel

from openhands.server.modules.conversation import conversation_module

app = APIRouter(prefix='/api/usecases')


class GetUsecasesRequest(BaseModel):
    page: int = 1
    limit: int = 10
    conversation_ids: list[str] = []
    prioritized_usecase_ids: list[str] = []


@app.get('')
async def get_usecases(
    request: Request, filter_query: Annotated[GetUsecasesRequest, Query()]
):
    return await conversation_module._get_list_conversations(
        **filter_query.model_dump(), published=True
    )
