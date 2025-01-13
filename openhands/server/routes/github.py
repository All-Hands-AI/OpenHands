import requests
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from openhands.server.shared import openhands_config
from openhands.utils.async_utils import call_sync_from_async

app = APIRouter(prefix='/api/github')


@app.get('/repositories')
async def get_github_repositories(
    request: Request,
    page: int = 1,
    per_page: int = 10,
    sort: str = 'pushed',
    installation_id: int | None = None,
):
    # Extract the GitHub token from the headers
    github_token = request.headers.get('X-GitHub-Token')
    if not github_token:
        raise HTTPException(status_code=400, detail='Missing X-GitHub-Token header')

    openhands_config.verify_github_repo_list(installation_id)

    # Add query parameters
    params: dict[str, str] = {
        'page': str(page),
        'per_page': str(per_page),
    }
    # Construct the GitHub API URL
    if installation_id:
        github_api_url = (
            f'https://api.github.com/user/installations/{installation_id}/repositories'
        )
    else:
        github_api_url = 'https://api.github.com/user/repos'
        params['sort'] = sort

    # Set the authorization header with the GitHub token
    headers = {
        'Authorization': f'Bearer {github_token}',
        'Accept': 'application/vnd.github.v3+json',
    }

    # Fetch repositories from GitHub
    try:
        response = await call_sync_from_async(
            requests.get, github_api_url, headers=headers, params=params
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
async def get_github_user(request: Request):
    github_token = request.headers.get('X-GitHub-Token')
    if not github_token:
        raise HTTPException(status_code=400, detail='Missing X-GitHub-Token header')

    headers = {
        'Authorization': f'Bearer {github_token}',
        'Accept': 'application/vnd.github.v3+json',
    }

    try:
        response = await call_sync_from_async(
            requests.get, 'https://api.github.com/user', headers=headers
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


@app.get('/installations')
async def get_github_installation_ids(request: Request):
    github_token = request.headers.get('X-GitHub-Token')
    if not github_token:
        raise HTTPException(status_code=400, detail='Missing X-GitHub-Token header')

    headers = {
        'Authorization': f'Bearer {github_token}',
        'Accept': 'application/vnd.github.v3+json',
    }

    try:
        response = await call_sync_from_async(
            requests.get, 'https://api.github.com/user/installations', headers=headers
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=response.status_code if response else 500,
            detail=f'Error fetching installations: {str(e)}',
        )

    data = response.json()
    ids = [installation['id'] for installation in data['installations']]
    json_response = JSONResponse(content=ids)
    response.close()

    return json_response


@app.get('/search/repositories')
async def search_github_repositories(
    request: Request,
    query: str,
    per_page: int = 5,
    sort: str = 'stars',
    order: str = 'desc',
):
    github_token = request.headers.get('X-GitHub-Token')
    if not github_token:
        raise HTTPException(status_code=400, detail='Missing X-GitHub-Token header')

    headers = {
        'Authorization': f'Bearer {github_token}',
        'Accept': 'application/vnd.github.v3+json',
    }

    params = {
        'q': query,
        'per_page': per_page,
        'sort': sort,
        'order': order,
    }

    try:
        response = await call_sync_from_async(
            requests.get,
            'https://api.github.com/search/repositories',
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
