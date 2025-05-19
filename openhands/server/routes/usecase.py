from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field, ValidationError, validator

from openhands.server.modules.conversation import conversation_module
from openhands.server.static import SortBy

app = APIRouter(prefix='/api/usecases')


def usecase_query_dependency(request: Request):
    try:
        return GetUsecasesRequest(**dict(request.query_params))
    except ValidationError as exc:
        errors = {}
        for error in exc.errors():
            loc = error.get('loc', [])

            field = loc[-1] if loc else 'general'
            if error.get('type') == 'enum':
                errors[field] = 'Invalid value'
            else:
                errors[field] = 'Invalid input'
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=errors)


class GetUsecasesRequest(BaseModel):
    page: int = Field(default=1, ge=1, description='Page number, starting from 1')
    limit: int = Field(default=10, ge=1, le=100, description='Items per page, max 100')
    conversation_ids: list[str] = []
    prioritized_usecase_ids: list[str] = []
    sort_by: SortBy = SortBy.total_view_7d

    @validator('limit')
    def validate_limit(cls, v):
        if v > 100:
            return 100
        return v


@app.get('')
async def get_usecases(
    request: Request,
    filter_query: GetUsecasesRequest = Depends(usecase_query_dependency),
):
    try:
        return await conversation_module._get_list_conversations(
            **filter_query.model_dump(), published=True
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Failed to retrieve usecases',
        )
