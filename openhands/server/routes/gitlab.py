import asyncio

import requests
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from openhands.utils.async_utils import call_sync_from_async

app = APIRouter(prefix='/api/gitlab')
active_tasks: dict[str, asyncio.Task] = {}


def require_gitlab_token(request: Request):
    gitlab_token = request.headers.get('X-Gitlab-Token')
    if not gitlab_token:
        raise HTTPException(
            status_code=400,
            detail='Missing X-Gitlab-Token header',
        )
    return gitlab_token


@app.get('/repositories')
async def get_gitlab_repositories(
    page: int = 1,
    per_page: int = 10,
    sort: str = 'updated_at',
    group_id: int | None = None,
    gitlab_token: str = Depends(require_gitlab_token),
):
    # Add query parameters
    params: dict[str, str] = {
        'page': str(page),
        'per_page': str(per_page),
    }
    # Construct the GitLab API URL
    if group_id:
        gitlab_api_url = f'https://gitlab.com/api/v4/groups/{group_id}/projects'
    else:
        gitlab_api_url = 'https://gitlab.com/api/v4/projects'
        params['order_by'] = sort
        params['owned'] = 'true'

    # Set the authorization header with the GitLab token
    headers = generate_gitlab_headers(gitlab_token)

    # Fetch repositories from GitLab
    try:
        response = await call_sync_from_async(
            requests.get, gitlab_api_url, headers=headers, params=params
        )
        response.raise_for_status()  # Raise an error for HTTP codes >= 400
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=response.status_code if response else 500,
            detail=f'Error fetching repositories: {str(e)}',
        )

    # Create response with the JSON content
    json_response = JSONResponse(content=response.json())
    response.close()

    # Forward the Link header if it exists
    if 'Link' in response.headers:
        json_response.headers['Link'] = response.headers['Link']

    return json_response


@app.get('/user')
async def get_gitlab_user(gitlab_token: str = Depends(require_gitlab_token)):
    headers = generate_gitlab_headers(gitlab_token)
    try:
        response = await call_sync_from_async(
            requests.get, 'https://gitlab.com/api/v4/user', headers=headers
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=response.status_code if response else 500,
            detail=f'Error fetching user: {str(e)}',
        )

    json_response = JSONResponse(content=response.json())
    response.close()

    return json_response


@app.get('/search/repositories')
async def search_gitlab_repositories(
    query: str,
    per_page: int = 5,
    sort: str = 'star_count',
    order: str = 'desc',
    gitlab_token: str = Depends(require_gitlab_token),
):
    headers = generate_gitlab_headers(gitlab_token)
    params = {
        'search': query,
        'per_page': per_page,
        'sort': sort,
        'order': order,
        'owned': True,
    }

    try:
        response = await call_sync_from_async(
            requests.get,
            'https://gitlab.com/api/v4/projects',
            headers=headers,
            params=params,
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=response.status_code if response else 500,
            detail=f'Error searching repositories: {str(e)}',
        )

    json_response = JSONResponse(content=response.json())
    response.close()

    return json_response


def generate_gitlab_headers(token: str) -> dict[str, str]:
    return {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/json',
    }
