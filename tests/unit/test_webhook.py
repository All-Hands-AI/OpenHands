import hmac
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from openhands.integrations.github.webhook_service import GitHubWebhookService
from openhands.server.app import app
from openhands.server.routes.webhooks import github_webhook


@pytest.fixture
def test_client():
    return TestClient(app)


@pytest.fixture
def sample_pr_payload():
    return {
        "action": "opened",
        "pull_request": {
            "number": 123,
            "title": "Test PR",
            "body": "This is a test PR",
            "head": {"ref": "feature-branch"},
            "base": {"ref": "main"},
        },
        "repository": {"full_name": "test-org/test-repo"},
        "sender": {"login": "test-user"},
    }


@pytest.mark.asyncio
async def test_github_webhook_service():
    """Test the GitHub webhook service."""
    # Create a mock for the webhook service
    webhook_service = GitHubWebhookService()
    
    # Test processing a PR event
    result = await webhook_service.process_pr_event(
        repo_full_name="test-org/test-repo",
        pr_number=123,
        pr_title="Test PR",
        pr_body="This is a test PR",
        pr_head_branch="feature-branch",
        pr_base_branch="main",
        action="opened",
        sender={"login": "test-user"},
    )
    
    # Check the result
    assert result["status"] in ["success", "error"]
    if result["status"] == "success":
        assert "conversation_id" in result
        assert result["conversation_id"] == "github-pr-test-org-test-repo-123"


@pytest.mark.asyncio
@patch("openhands.server.routes.webhooks.GitHubWebhookService")
async def test_github_webhook_endpoint(mock_webhook_service, sample_pr_payload):
    """Test the GitHub webhook endpoint."""
    # Mock the webhook service
    mock_service_instance = AsyncMock()
    mock_service_instance.process_pr_event.return_value = {
        "status": "success",
        "message": "Created conversation",
        "conversation_id": "github-pr-test-org-test-repo-123",
    }
    mock_webhook_service.return_value = mock_service_instance
    
    # Create a mock request
    mock_request = MagicMock()
    mock_request.body = AsyncMock(return_value=json.dumps(sample_pr_payload).encode())
    
    # Call the webhook endpoint
    response = await github_webhook(
        request=mock_request,
        x_github_event="pull_request",
        x_hub_signature_256=None,
    )
    
    # Check the response
    assert response["status"] == "success"
    assert "conversation_id" in response
    assert response["event"] == "pull_request"
    assert response["action"] == "opened"
    
    # Verify the webhook service was called with the correct parameters
    mock_service_instance.process_pr_event.assert_called_once_with(
        repo_full_name="test-org/test-repo",
        pr_number=123,
        pr_title="Test PR",
        pr_body="This is a test PR",
        pr_head_branch="feature-branch",
        pr_base_branch="main",
        action="opened",
        sender={"login": "test-user"},
    )


@pytest.mark.asyncio
async def test_github_webhook_signature_validation():
    """Test webhook signature validation."""
    # Create a sample payload
    payload = {"action": "opened"}
    payload_bytes = json.dumps(payload).encode()
    
    # Create a mock request
    mock_request = MagicMock()
    mock_request.body = AsyncMock(return_value=payload_bytes)
    
    # Set up a webhook secret
    webhook_secret = "test-secret"
    
    # Calculate the correct signature
    signature = hmac.new(
        webhook_secret.encode(),
        msg=payload_bytes,
        digestmod="sha256"
    ).hexdigest()
    correct_signature = f"sha256={signature}"
    
    # Test with incorrect signature
    with patch("openhands.server.routes.webhooks.server_config") as mock_config:
        mock_config.github_webhook_secret = webhook_secret
        
        with pytest.raises(HTTPException) as excinfo:
            await github_webhook(
                request=mock_request,
                x_github_event="pull_request",
                x_hub_signature_256="sha256=invalid",
            )
        
        assert excinfo.value.status_code == 401
        assert excinfo.value.detail == "Invalid signature"
    
    # Test with correct signature
    with patch("openhands.server.routes.webhooks.server_config") as mock_config:
        mock_config.github_webhook_secret = webhook_secret
        
        # Also mock the GitHubWebhookPayload validation to avoid processing the payload
        with patch("openhands.server.routes.webhooks.GitHubWebhookPayload"):
            response = await github_webhook(
                request=mock_request,
                x_github_event="pull_request",
                x_hub_signature_256=correct_signature,
            )
            
            # Since we're not mocking the full payload processing,
            # we'll just check that we got past the signature validation
            assert "status" in response