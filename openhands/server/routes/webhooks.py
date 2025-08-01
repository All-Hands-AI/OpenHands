import hmac
import json
from typing import Any, Optional

from fastapi import APIRouter, Header, HTTPException, Request, status
from pydantic import BaseModel, Field

from openhands.core.logger import openhands_logger as logger
from openhands.integrations.github.webhook_service import GitHubWebhookService
from openhands.server.dependencies import get_dependencies
from openhands.server.shared import server_config

app = APIRouter(prefix='/api/webhooks', dependencies=get_dependencies())


class GitHubWebhookPayload(BaseModel):
    """Model for GitHub webhook payload."""

    action: str = Field(..., description='The action that was performed')
    pull_request: Optional[dict[str, Any]] = Field(
        None, description='Pull request data'
    )
    repository: dict[str, Any] = Field(..., description='Repository data')
    sender: dict[str, Any] = Field(..., description='User who triggered the event')


@app.post('/github')
async def github_webhook(
    request: Request,
    x_github_event: str = Header(..., description='GitHub event type'),
    x_hub_signature_256: Optional[str] = Header(
        None, description='GitHub webhook signature'
    ),
):
    """
    Handle GitHub webhook events.

    This endpoint receives webhook events from GitHub, validates them,
    and triggers the appropriate OpenHands automation process.

    Currently supported events:
    - pull_request (opened, synchronize, reopened)
    """
    # Get the raw request body
    body = await request.body()

    # Verify webhook signature if configured
    webhook_secret = server_config.github_webhook_secret
    if webhook_secret and x_hub_signature_256:
        signature = hmac.new(
            webhook_secret.encode(), msg=body, digestmod='sha256'
        ).hexdigest()
        expected_signature = f'sha256={signature}'

        if not hmac.compare_digest(expected_signature, x_hub_signature_256):
            logger.warning(
                'Invalid GitHub webhook signature', extra={'event': x_github_event}
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid signature'
            )

    # Parse the payload
    try:
        payload_dict = json.loads(body)

        # Only process pull_request events for now
        if x_github_event == 'pull_request':
            payload = GitHubWebhookPayload(**payload_dict)

            # Only process certain PR actions
            if payload.action in ['opened', 'synchronize', 'reopened']:
                # Extract relevant information
                repo_full_name = str(payload.repository.get('full_name', ''))
                pr_number = (
                    int(payload.pull_request.get('number', 0))
                    if payload.pull_request
                    else 0
                )
                pr_title = (
                    str(payload.pull_request.get('title', ''))
                    if payload.pull_request
                    else ''
                )
                pr_body = (
                    payload.pull_request.get('body') if payload.pull_request else None
                )

                # Get head and base branch with proper type checking
                head_dict = (
                    payload.pull_request.get('head', {}) if payload.pull_request else {}
                )
                base_dict = (
                    payload.pull_request.get('base', {}) if payload.pull_request else {}
                )
                pr_head_branch = str(head_dict.get('ref', ''))
                pr_base_branch = str(base_dict.get('ref', ''))

                logger.info(
                    f'Processing GitHub PR webhook: {repo_full_name}#{pr_number}',
                    extra={
                        'event': x_github_event,
                        'action': payload.action,
                        'repo': repo_full_name,
                        'pr_number': pr_number,
                    },
                )

                # Process the PR event using the webhook service
                webhook_service = GitHubWebhookService()
                result = await webhook_service.process_pr_event(
                    repo_full_name=repo_full_name,
                    pr_number=pr_number,
                    pr_title=pr_title,
                    pr_body=pr_body,
                    pr_head_branch=pr_head_branch,
                    pr_base_branch=pr_base_branch,
                    action=payload.action,
                    sender=payload.sender,
                )

                # Add event info to the result
                result['event'] = x_github_event
                result['action'] = payload.action

                return result

        return {
            'status': 'ignored',
            'message': f'Event {x_github_event} with action {payload_dict.get("action")} not processed',
            'event': x_github_event,
        }

    except Exception as e:
        logger.error(
            f'Error processing GitHub webhook: {str(e)}',
            extra={'event': x_github_event},
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Error processing webhook: {str(e)}',
        )
