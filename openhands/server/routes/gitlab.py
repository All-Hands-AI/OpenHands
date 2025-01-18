import asyncio
import json
import os
import re
import subprocess
import tempfile
from typing import Any

import requests
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from openhands.core.logger import openhands_logger as logger
from openhands.resolver.io_utils import (
    load_single_resolver_output,
)
from openhands.server.shared import openhands_config
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
    openhands_config.verify_github_repo_list(group_id)

    # Add query parameters
    params: dict[str, str] = {
        'page': str(page),
        'per_page': str(per_page),
    }
    # Construct the GitHub API URL
    if group_id:
        github_api_url = f'https://gitlab.com/api/v4/groups/{group_id}/projects'
    else:
        github_api_url = 'https://gitlab.com/api/v4/projects'
        params['order_by'] = sort
        params['owned'] = 'true'

    # Set the authorization header with the GitHub token
    headers = generate_gitlab_headers(gitlab_token)

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
async def get_github_user(gitlab_token: str = Depends(require_gitlab_token)):
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


@app.get('/installations')
async def get_github_installation_ids(
    gitlab_token: str = Depends(require_gitlab_token),
):
    headers = generate_gitlab_headers(gitlab_token)
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


@app.post('/hooks')
async def gitlab_webhook(
    request: Request, gitlab_token: str = Depends(require_gitlab_token)
):
    try:
        payload = await request.json()
        task_id = payload.get('object_attributes', {}).get('id', {})
        if f'{task_id}' in active_tasks:
            task = active_tasks[f'{task_id}']
            if not task.done():
                return {'status': 'running', 'task_id': task_id}

        task = asyncio.create_task(process_resolver(request, gitlab_token))
        active_tasks[f'{task_id}'] = task

        task.add_done_callback(lambda t: active_tasks.pop(task_id, None))
        logger.info(
            f'Created new webhook task {task_id}. Active tasks: {len(active_tasks)}'
        )

        return {'status': 'success', 'task_id': task_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Error: {str(e)}')


@app.get('/hooks/status/{task_id}')
async def get_task_status(task_id: str):
    if task_id in active_tasks:
        task = active_tasks[task_id]
        return {
            'status': 'running' if not task.done() else 'completed',
            'error': str(task.exception())
            if task.done() and task.exception()
            else None,
        }
    return {'status': 'not_found'}


async def run_subprocess_async(
    cmd: list,
) -> tuple[asyncio.subprocess.Process, bytes, bytes]:
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env={**os.environ},
    )
    stdout, stderr = await process.communicate()

    if stdout:
        logger.info(stdout.decode().strip())
    if stderr:
        logger.error(stderr.decode().strip())

    return process, stdout, stderr


async def process_resolver(request: Request, gitlab_token: str):
    headers = generate_gitlab_headers(gitlab_token)

    try:
        payload = await request.json()
        gitlab_event = request.headers.get('X-Gitlab-Event')
        openhands_macro = request.headers.get(
            'X-Gitlab-Openhands-Macro', '@openhands-agent'
        )
        max_iterations = request.headers.get('X-Gitlab-Max-Iterations', 50)
        llm_model = request.headers.get('X-Gitlab-Llm-Model', '')
        llm_api_key = request.headers.get('X-Gitlab-Llm-Api-Key', '')
        llm_base_url = request.headers.get('X-Gitlab-Llm-Base-Url', '')
        repo = payload.get('project').get('path_with_namespace')
        username = payload.get('user').get('username')
        attributes = payload.get('object_attributes', {})
        action = attributes.get('action', '')
        comment_id = 'none'
        project_id = payload.get('project', {}).get('id')
        issue_type = None
        issue_number = None

        if action == '' or action == 'close':
            logger.error(f'{gitlab_event} is closed.')
            return

        if gitlab_event == 'Issue Hook' and attributes.get('state', '') != 'closed':
            for label in payload['labels']:
                if label['title'] in ('fix-me', 'fix-me-experimental'):
                    print(f"Resolver Trigger: {label['title']}")

                    issue_type = 'issue'
                    issue_number = attributes.get('iid')
        elif gitlab_event == 'Note Hook':
            author_id = attributes.get('author_id')

            try:
                response = await call_sync_from_async(
                    requests.get,
                    f'https://gitlab.com/api/v4/projects/{project_id}/members/all',
                    headers=headers,
                )
                response.raise_for_status()
                author: dict = next(
                    (item for item in response.json() if item['id'] == author_id), {}
                )

                if (
                    openhands_macro in attributes.get('note')
                    and author.get('state') == 'active'
                    and author.get('access_level', 0) >= 20
                ):
                    if payload.get('merge_request', {}).get('state', '') == 'closed':
                        logger.error('Invalid Event')
                        return

                    print(f'Resolver Trigger: {openhands_macro}')

                    if attributes.get('noteable_type', '') == 'MergeRequest':
                        issue_type = 'pr'
                        issue_number = payload.get('merge_request').get('iid')
                    else:
                        issue_type = 'issue'
                        issue_number = payload.get('issue').get('iid')

                    comment_id = attributes.get('id', 'none')
            except requests.exceptions.RequestException as e:
                raise HTTPException(
                    status_code=response.status_code if response else 500,
                    detail=f'Error fetching user: {str(e)}',
                )
            finally:
                response.close()
        else:
            logger.error('Invalid Event')
            return

        if issue_type is None or issue_number is None:
            logger.error('Invalid Event')
            return

        create_comment(
            gitlab_token,
            project_id,
            issue_number,
            f'[OpenHands](https://github.com/All-Hands-AI/OpenHands) started fixing the {issue_type}!',
        )
        with tempfile.TemporaryDirectory() as output_dir:
            print('Temporary directory created at:', output_dir)

        try:
            logger.info('Attempt to resolve issue')
            os.environ['LLM_MODEL'] = llm_model
            os.environ['LLM_API_KEY'] = llm_api_key
            os.environ['LLM_BASE_URL'] = llm_base_url
            _, stdout, _ = await run_subprocess_async(
                [
                    'python',
                    '-m',
                    'openhands.resolver.resolve_issue',
                    '--repo',
                    f'{repo}',
                    '--token',
                    gitlab_token,
                    '--username',
                    username,
                    '--issue-number',
                    f'{issue_number}',
                    '--issue-type',
                    issue_type,
                    '--max-iterations',
                    f'{max_iterations}',
                    '--comment-id',
                    f'{comment_id}',
                    '--output-dir',
                    output_dir,
                ]
            )

            logger.info('Check resolution result')
            output_file = os.path.join(output_dir, 'output.jsonl')
            resolver_output = load_single_resolver_output(
                output_file, int(issue_number)
            )

            logger.info('Create draft PR or push branch')
            no_changes_message = (
                f'No changes to commit for issue #{issue_number}. Skipping commit.'
            )

            if resolver_output.success:
                _, stdout, _ = await run_subprocess_async(
                    [
                        'python',
                        '-m',
                        'openhands.resolver.send_pull_request',
                        '--token',
                        gitlab_token,
                        '--username',
                        username,
                        '--issue-number',
                        f'{issue_number}',
                        '--pr-type',
                        'draft',
                        '--output-dir',
                        output_dir,
                    ]
                )

                if stdout:
                    output = stdout.decode().strip()
            else:
                _, stdout, _ = await run_subprocess_async(
                    [
                        'python',
                        '-m',
                        'openhands.resolver.send_pull_request',
                        '--repo',
                        f'{repo}',
                        '--token',
                        gitlab_token,
                        '--username',
                        username,
                        '--issue-number',
                        f'{issue_number}',
                        '--pr-type',
                        'branch',
                        '--send-on-failure',
                        '--output-dir',
                        output_dir,
                    ]
                )

                if stdout:
                    output = stdout.decode().strip()

            if no_changes_message in output:
                create_comment(
                    gitlab_token,
                    project_id,
                    issue_number,
                    'The resolver to fix this issue encountered an error. Openhands failed to create any code changes.',
                )

            if resolver_output.success:
                match = re.search(r'merge_requests/(\d+)', output)

                if match:
                    pr_number = match.group(1)

                    if pr_number:
                        create_comment(
                            gitlab_token,
                            project_id,
                            issue_number,
                            f'A potential fix has been generated and a draft PR #{pr_number} has been created. Please review the changes.',
                        )
            else:
                match = re.search(r'compare/main\.\.\.(.+)$', output)

                if match:
                    branch_name = match.group(1)
                    body = f'An attempt was made to automatically fix this issue, but it was unsuccessful. A branch named {branch_name} has been created with the attempted changes. You can view the branch [here](https://gitlab.com/{repo}/-/tree/{branch_name}). Manual intervention may be required.'

                    if branch_name:
                        create_comment(gitlab_token, project_id, issue_number, body)

        except subprocess.CalledProcessError as e:
            return {'error': f'Script execution failed: {e.stderr}'}
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail='Invalid JSON payload')
    except Exception as e:
        import traceback

        # Alternatively, get the stack trace as a string
        error_details = traceback.format_exc()
        print(f'Full traceback:\n{error_details}')
        raise HTTPException(status_code=500, detail=f'{e}')

    return 'success'


def create_comment(token: str, project_id: str, issue_number: Any | None, body: str):
    comment_url = (
        f'https://gitlab.com/api/v4/projects/{project_id}/issues/{issue_number}/notes'
    )
    comment_data = {'body': body}
    comment_response = requests.post(
        comment_url, headers=generate_gitlab_headers(token), json=comment_data
    )
    if comment_response.status_code != 201:
        print(
            f'Failed to post comment: {comment_response.status_code} {comment_response.text}'
        )


def generate_gitlab_headers(token: str) -> dict[str, str]:
    return {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/json',
    }
