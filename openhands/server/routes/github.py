from typing import Literal

import requests
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import JSONResponse

from openhands.server.shared import openhands_config
from openhands.utils.async_utils import call_sync_from_async

app = APIRouter(prefix='/api')

GITHUB_API_BASE = 'https://api.github.com'
GITHUB_API_VERSION = '2022-11-28'


@app.get('/github/repositories')
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


@app.get('/github/installations')
async def get_github_installations(request: Request):
    """Get GitHub App installations for the authenticated user"""
    github_token = request.headers.get('X-GitHub-Token')
    if not github_token:
        raise HTTPException(status_code=400, detail='Missing X-GitHub-Token header')

    headers = {
        'Authorization': f'Bearer {github_token}',
        'Accept': 'application/vnd.github.v3+json',
        'X-GitHub-Api-Version': GITHUB_API_VERSION,
    }

    try:
        response = await call_sync_from_async(
            requests.get, f'{GITHUB_API_BASE}/user/installations', headers=headers
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=response.status_code if response else 500,
            detail=f'Error fetching installations: {str(e)}',
        )

    return JSONResponse(content=response.json())


@app.get('/github/user')
async def get_github_user(request: Request):
    """Get authenticated GitHub user information"""
    github_token = request.headers.get('X-GitHub-Token')
    if not github_token:
        raise HTTPException(status_code=400, detail='Missing X-GitHub-Token header')

    headers = {
        'Authorization': f'Bearer {github_token}',
        'Accept': 'application/vnd.github.v3+json',
        'X-GitHub-Api-Version': GITHUB_API_VERSION,
    }

    try:
        response = await call_sync_from_async(
            requests.get, f'{GITHUB_API_BASE}/user', headers=headers
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=response.status_code if response else 500,
            detail=f'Error fetching user: {str(e)}',
        )

    data = response.json()
    return JSONResponse(
        content={
            'id': data['id'],
            'login': data['login'],
            'avatar_url': data['avatar_url'],
            'company': data.get('company'),
            'name': data.get('name'),
            'email': data.get('email'),
        }
    )


@app.get('/github/search/repositories')
async def search_github_repositories(
    request: Request,
    query: str,
    per_page: int = Query(default=5, le=100),
    sort: Literal['', 'updated', 'stars', 'forks'] = 'stars',
    order: Literal['desc', 'asc'] = 'desc',
):
    """Search public GitHub repositories"""
    github_token = request.headers.get('X-GitHub-Token')
    if not github_token:
        raise HTTPException(status_code=400, detail='Missing X-GitHub-Token header')

    headers = {
        'Authorization': f'Bearer {github_token}',
        'Accept': 'application/vnd.github.v3+json',
        'X-GitHub-Api-Version': GITHUB_API_VERSION,
    }

    params = {'q': query, 'per_page': str(per_page), 'sort': sort, 'order': order}

    try:
        response = await call_sync_from_async(
            requests.get,
            f'{GITHUB_API_BASE}/search/repositories',
            headers=headers,
            params=params,
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=response.status_code if response else 500,
            detail=f'Error searching repositories: {str(e)}',
        )

    return JSONResponse(content=response.json())


@app.get('/github/repos/{owner}/{repo}/commits')
async def get_github_commits(
    request: Request, owner: str, repo: str, per_page: int = Query(default=1, le=100)
):
    """Get latest commits for a GitHub repository"""
    github_token = request.headers.get('X-GitHub-Token')
    if not github_token:
        raise HTTPException(status_code=400, detail='Missing X-GitHub-Token header')

    headers = {
        'Authorization': f'Bearer {github_token}',
        'Accept': 'application/vnd.github.v3+json',
        'X-GitHub-Api-Version': GITHUB_API_VERSION,
    }

    params = {'per_page': str(per_page)}

    try:
        response = await call_sync_from_async(
            requests.get,
            f'{GITHUB_API_BASE}/repos/{owner}/{repo}/commits',
            headers=headers,
            params=params,
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        response = getattr(e, 'response', None)
        if response and response.status_code == 409:
            # Repository is empty, no commits yet
            return JSONResponse(content=[])
        raise HTTPException(
            status_code=getattr(getattr(e, 'response', None), 'status_code', 500),
            detail=f'Error fetching commits: {str(e)}',
        )

    return JSONResponse(content=response.json())
