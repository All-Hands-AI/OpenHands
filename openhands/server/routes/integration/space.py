from fastapi import APIRouter, HTTPException, Request, status

from openhands.server.modules.space import SpaceModule

space_router = APIRouter(prefix='/spaces')


@space_router.get('')
async def get_list_space(
    request: Request, offset: int = 0, limit: int = 10, title: str | None = None
) -> dict | None:
    space_module = SpaceModule(request.headers.get('Authorization'))
    try:
        list_space, pagination = await space_module.get_list_space(offset, limit, title)
    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Unauthorized',
        )

    return {
        'data': list_space,
        'pagination': pagination,
        'status': 'Get list spaces success',
    }


@space_router.get('/{space_id}')
async def get_space_detail(
    request: Request,
    space_id: str,
) -> dict | None:
    space_module = SpaceModule(request.headers.get('Authorization'))
    try:
        space_detail = await space_module.get_space_detail(space_id)
    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Space not found',
        )

    return {
        'data': space_detail,
        'status': 'Get space detail success',
    }


@space_router.get('/{space_id}/sections')
async def get_space_sections(
    request: Request,
    space_id: str,
) -> dict | None:
    space_module = SpaceModule(request.headers.get('Authorization'))
    try:
        # check space exist and user have permission to access this space
        await space_module.get_space_detail(space_id)
        space_sections = await space_module.get_list_sections(space_id)
    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Space not found',
        )

    return {
        'data': space_sections,
        'status': 'Get space sections success',
    }
