import requests
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from openhands.server.shared import openhands_config
from openhands.server.types import AppMode

app = APIRouter(prefix='/api')


@app.get('/github/repositories')
def get_github_repositories(
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

    if installation_id is None and openhands_config.APP_MODE == AppMode.SAAS:
        raise HTTPException(
            status_code=400,
            detail='Missing installation_id. This field is required.',
        )

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
        response = requests.get(github_api_url, headers=headers, params=params)
        response.raise_for_status()  # Raise an error for HTTP codes >= 400
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=response.status_code if response else 500,
            detail=f'Error fetching repositories: {str(e)}',
        )

    # Return the JSON response
    return JSONResponse(content=response.json())
