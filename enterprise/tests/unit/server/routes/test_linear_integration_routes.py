import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, Request, status
from fastapi.responses import RedirectResponse
from pydantic import ValidationError
from server.auth.saas_user_auth import SaasUserAuth
from server.routes.integration.linear import (
    LinearLinkCreate,
    LinearWorkspaceCreate,
    _handle_workspace_link_creation,
    _validate_workspace_update_permissions,
    create_linear_workspace,
    create_workspace_link,
    get_current_workspace_link,
    linear_callback,
    linear_events,
    unlink_workspace,
    validate_workspace_integration,
)


@pytest.fixture
def mock_request():
    req = MagicMock(spec=Request)
    req.headers = {}
    req.cookies = {}
    req.app.state.redis = MagicMock()
    return req


@pytest.fixture
def mock_linear_manager():
    manager = MagicMock()
    manager.integration_store = AsyncMock()
    manager.validate_request = AsyncMock()
    return manager


@pytest.fixture
def mock_token_manager():
    return MagicMock()


@pytest.fixture
def mock_redis_client():
    client = MagicMock()
    client.exists.return_value = False
    client.setex.return_value = True
    return client


@pytest.fixture
def mock_user_auth():
    auth = AsyncMock(spec=SaasUserAuth)
    auth.get_user_id = AsyncMock(return_value='test_user_id')
    auth.get_user_email = AsyncMock(return_value='test@example.com')
    return auth


# Test Pydantic Model Validations
class TestLinearWorkspaceCreateValidation:
    def test_valid_workspace_create(self):
        data = LinearWorkspaceCreate(
            workspace_name='test-workspace',
            webhook_secret='secret123',
            svc_acc_email='test@example.com',
            svc_acc_api_key='api_key_123',
            is_active=True,
        )
        assert data.workspace_name == 'test-workspace'
        assert data.svc_acc_email == 'test@example.com'

    def test_invalid_workspace_name(self):
        with pytest.raises(ValidationError) as exc_info:
            LinearWorkspaceCreate(
                workspace_name='test workspace!',  # Contains space and special char
                webhook_secret='secret123',
                svc_acc_email='test@example.com',
                svc_acc_api_key='api_key_123',
            )
        assert 'workspace_name can only contain alphanumeric characters' in str(
            exc_info.value
        )

    def test_invalid_email(self):
        with pytest.raises(ValidationError) as exc_info:
            LinearWorkspaceCreate(
                workspace_name='test-workspace',
                webhook_secret='secret123',
                svc_acc_email='invalid-email',
                svc_acc_api_key='api_key_123',
            )
        assert 'svc_acc_email must be a valid email address' in str(exc_info.value)

    def test_webhook_secret_with_spaces(self):
        with pytest.raises(ValidationError) as exc_info:
            LinearWorkspaceCreate(
                workspace_name='test-workspace',
                webhook_secret='secret with spaces',
                svc_acc_email='test@example.com',
                svc_acc_api_key='api_key_123',
            )
        assert 'webhook_secret cannot contain spaces' in str(exc_info.value)

    def test_api_key_with_spaces(self):
        with pytest.raises(ValidationError) as exc_info:
            LinearWorkspaceCreate(
                workspace_name='test-workspace',
                webhook_secret='secret123',
                svc_acc_email='test@example.com',
                svc_acc_api_key='api key with spaces',
            )
        assert 'svc_acc_api_key cannot contain spaces' in str(exc_info.value)


class TestLinearLinkCreateValidation:
    def test_valid_link_create(self):
        data = LinearLinkCreate(workspace_name='test-workspace')
        assert data.workspace_name == 'test-workspace'

    def test_invalid_workspace_name(self):
        with pytest.raises(ValidationError) as exc_info:
            LinearLinkCreate(workspace_name='invalid workspace!')
        assert 'workspace can only contain alphanumeric characters' in str(
            exc_info.value
        )


# Test linear_events error scenarios
@pytest.mark.asyncio
@patch('server.routes.integration.linear.linear_manager', new_callable=AsyncMock)
@patch('server.routes.integration.linear.redis_client', new_callable=MagicMock)
async def test_linear_events_processing_success(mock_redis, mock_manager, mock_request):
    with patch('server.routes.integration.linear.LINEAR_WEBHOOKS_ENABLED', True):
        mock_manager.validate_request.return_value = (
            True,
            'sig123',
            {'test': 'payload'},
        )
        mock_redis.exists.return_value = False

        background_tasks = MagicMock()
        response = await linear_events(mock_request, background_tasks)

        assert response.status_code == 200
        body = json.loads(response.body)
        assert body['success'] is True
        mock_redis.setex.assert_called_once_with('linear:sig123', 60, 1)
        background_tasks.add_task.assert_called_once()


@pytest.mark.asyncio
@patch('server.routes.integration.linear.linear_manager', new_callable=AsyncMock)
@patch('server.routes.integration.linear.redis_client', new_callable=MagicMock)
async def test_linear_events_general_exception(mock_redis, mock_manager, mock_request):
    with patch('server.routes.integration.linear.LINEAR_WEBHOOKS_ENABLED', True):
        mock_manager.validate_request.side_effect = Exception('Unexpected error')

        response = await linear_events(mock_request, MagicMock())

        assert response.status_code == 500
        body = json.loads(response.body)
        assert 'Internal server error processing webhook' in body['error']


# Test create_linear_workspace error scenarios
@pytest.mark.asyncio
@patch('server.routes.integration.linear.get_user_auth')
async def test_create_linear_workspace_auth_failure(mock_get_auth, mock_request):
    mock_get_auth.side_effect = HTTPException(status_code=401, detail='Unauthorized')

    workspace_data = LinearWorkspaceCreate(
        workspace_name='test-workspace',
        webhook_secret='secret',
        svc_acc_email='svc@test.com',
        svc_acc_api_key='key',
    )

    with pytest.raises(HTTPException) as exc_info:
        await create_linear_workspace(mock_request, workspace_data)
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
@patch('server.routes.integration.linear.get_user_auth')
@patch('server.routes.integration.linear.redis_client')
async def test_create_linear_workspace_redis_failure(
    mock_redis, mock_get_auth, mock_request, mock_user_auth
):
    mock_get_auth.return_value = mock_user_auth
    mock_redis.setex.return_value = False  # Redis operation failed

    workspace_data = LinearWorkspaceCreate(
        workspace_name='test-workspace',
        webhook_secret='secret',
        svc_acc_email='svc@test.com',
        svc_acc_api_key='key',
    )

    with pytest.raises(HTTPException) as exc_info:
        await create_linear_workspace(mock_request, workspace_data)
    assert exc_info.value.status_code == 500
    assert 'Failed to create integration session' in exc_info.value.detail


@pytest.mark.asyncio
@patch('server.routes.integration.linear.get_user_auth')
async def test_create_linear_workspace_unexpected_error(mock_get_auth, mock_request):
    mock_get_auth.side_effect = Exception('Unexpected error')

    workspace_data = LinearWorkspaceCreate(
        workspace_name='test-workspace',
        webhook_secret='secret',
        svc_acc_email='svc@test.com',
        svc_acc_api_key='key',
    )

    with pytest.raises(HTTPException) as exc_info:
        await create_linear_workspace(mock_request, workspace_data)
    assert exc_info.value.status_code == 500
    assert 'Failed to create workspace' in exc_info.value.detail


# Test create_workspace_link error scenarios
@pytest.mark.asyncio
@patch('server.routes.integration.linear.get_user_auth')
@patch('server.routes.integration.linear.redis_client')
async def test_create_workspace_link_redis_failure(
    mock_redis, mock_get_auth, mock_request, mock_user_auth
):
    mock_get_auth.return_value = mock_user_auth
    mock_redis.setex.return_value = False

    link_data = LinearLinkCreate(workspace_name='test-workspace')

    with pytest.raises(HTTPException) as exc_info:
        await create_workspace_link(mock_request, link_data)
    assert exc_info.value.status_code == 500
    assert 'Failed to create integration session' in exc_info.value.detail


@pytest.mark.asyncio
@patch('server.routes.integration.linear.get_user_auth')
async def test_create_workspace_link_unexpected_error(mock_get_auth, mock_request):
    mock_get_auth.side_effect = Exception('Unexpected error')

    link_data = LinearLinkCreate(workspace_name='test-workspace')

    with pytest.raises(HTTPException) as exc_info:
        await create_workspace_link(mock_request, link_data)
    assert exc_info.value.status_code == 500
    assert 'Failed to register user' in exc_info.value.detail


# Test linear_callback error scenarios
@pytest.mark.asyncio
@patch('server.routes.integration.linear.redis_client')
async def test_linear_callback_no_session(mock_redis, mock_request):
    mock_redis.get.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        await linear_callback(mock_request, 'code', 'state')
    assert exc_info.value.status_code == 400
    assert 'No active integration session found' in exc_info.value.detail


@pytest.mark.asyncio
@patch('server.routes.integration.linear.redis_client')
async def test_linear_callback_state_mismatch(mock_redis, mock_request):
    session_data = {'state': 'different_state'}
    mock_redis.get.return_value = json.dumps(session_data)

    with pytest.raises(HTTPException) as exc_info:
        await linear_callback(mock_request, 'code', 'wrong_state')
    assert exc_info.value.status_code == 400
    assert 'State mismatch. Possible CSRF attack' in exc_info.value.detail


@pytest.mark.asyncio
@patch('server.routes.integration.linear.redis_client')
@patch('requests.post')
async def test_linear_callback_token_fetch_failure(mock_post, mock_redis, mock_request):
    session_data = {'state': 'test_state'}
    mock_redis.get.return_value = json.dumps(session_data)
    mock_post.return_value = MagicMock(status_code=400, text='Token error')

    with pytest.raises(HTTPException) as exc_info:
        await linear_callback(mock_request, 'code', 'test_state')
    assert exc_info.value.status_code == 400
    assert 'Error fetching token' in exc_info.value.detail


@pytest.mark.asyncio
@patch('server.routes.integration.linear.redis_client')
@patch('requests.post')
async def test_linear_callback_workspace_fetch_failure(
    mock_post, mock_redis, mock_request
):
    session_data = {'state': 'test_state'}
    mock_redis.get.return_value = json.dumps(session_data)
    mock_post.side_effect = [
        MagicMock(status_code=200, json=lambda: {'access_token': 'token'}),
        MagicMock(status_code=400, text='Workspace error'),
    ]

    with pytest.raises(HTTPException) as exc_info:
        await linear_callback(mock_request, 'code', 'test_state')
    assert exc_info.value.status_code == 400
    assert 'Error fetching workspace' in exc_info.value.detail


@pytest.mark.asyncio
@patch('server.routes.integration.linear.redis_client')
@patch('requests.post')
async def test_linear_callback_unauthorized_workspace(
    mock_post, mock_redis, mock_request
):
    session_data = {'state': 'test_state', 'target_workspace': 'target-workspace'}
    mock_redis.get.return_value = json.dumps(session_data)
    mock_post.side_effect = [
        MagicMock(status_code=200, json=lambda: {'access_token': 'token'}),
        MagicMock(
            status_code=200,
            json=lambda: {
                'data': {'viewer': {'organization': {'urlKey': 'different-workspace'}}}
            },
        ),
    ]

    with pytest.raises(HTTPException) as exc_info:
        await linear_callback(mock_request, 'code', 'test_state')
    assert exc_info.value.status_code == 401
    assert 'User is not authorized to access workspace' in exc_info.value.detail


@pytest.mark.asyncio
@patch('server.routes.integration.linear.redis_client')
@patch('requests.post')
@patch('server.routes.integration.linear.linear_manager', new_callable=AsyncMock)
@patch(
    'server.routes.integration.linear._handle_workspace_link_creation',
    new_callable=AsyncMock,
)
async def test_linear_callback_workspace_integration_existing_workspace(
    mock_handle_link, mock_manager, mock_post, mock_redis, mock_request
):
    state = 'test_state'
    session_data = {
        'operation_type': 'workspace_integration',
        'keycloak_user_id': 'user1',
        'target_workspace': 'existing-space',
        'webhook_secret': 'secret',
        'svc_acc_email': 'email@test.com',
        'svc_acc_api_key': 'apikey',
        'is_active': True,
        'state': state,
    }
    mock_redis.get.return_value = json.dumps(session_data)
    mock_post.side_effect = [
        MagicMock(status_code=200, json=lambda: {'access_token': 'token'}),
        MagicMock(
            status_code=200,
            json=lambda: {
                'data': {'viewer': {'organization': {'urlKey': 'existing-space'}}}
            },
        ),
    ]

    # Mock existing workspace
    mock_workspace = MagicMock(id=1)
    mock_manager.integration_store.get_workspace_by_name.return_value = mock_workspace

    with patch('server.routes.integration.linear.token_manager') as mock_token_manager:
        with patch(
            'server.routes.integration.linear._validate_workspace_update_permissions'
        ) as mock_validate:
            mock_validate.return_value = mock_workspace
            mock_token_manager.encrypt_text.side_effect = lambda x: f'enc_{x}'

            response = await linear_callback(mock_request, 'code', state)

            assert isinstance(response, RedirectResponse)
            assert response.status_code == status.HTTP_302_FOUND
            mock_manager.integration_store.update_workspace.assert_called_once()
            mock_handle_link.assert_called_once_with('user1', None, 'existing-space')


@pytest.mark.asyncio
@patch('server.routes.integration.linear.redis_client')
@patch('requests.post')
async def test_linear_callback_invalid_operation_type(
    mock_post, mock_redis, mock_request
):
    session_data = {
        'operation_type': 'invalid_operation',
        'target_workspace': 'test-workspace',
        'keycloak_user_id': 'user1',  # Add missing field
        'state': 'test_state',
    }
    mock_redis.get.return_value = json.dumps(session_data)
    mock_post.side_effect = [
        MagicMock(status_code=200, json=lambda: {'access_token': 'token'}),
        MagicMock(
            status_code=200,
            json=lambda: {
                'data': {'viewer': {'organization': {'urlKey': 'test-workspace'}}}
            },
        ),
    ]

    with pytest.raises(HTTPException) as exc_info:
        await linear_callback(mock_request, 'code', 'test_state')
    assert exc_info.value.status_code == 400
    assert 'Invalid operation type' in exc_info.value.detail


# Test get_current_workspace_link error scenarios
@pytest.mark.asyncio
@patch('server.routes.integration.linear.get_user_auth')
@patch('server.routes.integration.linear.linear_manager', new_callable=AsyncMock)
async def test_get_current_workspace_link_user_not_found(
    mock_manager, mock_get_auth, mock_request, mock_user_auth
):
    mock_get_auth.return_value = mock_user_auth
    mock_manager.integration_store.get_user_by_active_workspace.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        await get_current_workspace_link(mock_request)
    assert exc_info.value.status_code == 404
    assert 'User is not registered for Linear integration' in exc_info.value.detail


@pytest.mark.asyncio
@patch('server.routes.integration.linear.get_user_auth')
@patch('server.routes.integration.linear.linear_manager', new_callable=AsyncMock)
async def test_get_current_workspace_link_workspace_not_found(
    mock_manager, mock_get_auth, mock_request, mock_user_auth
):
    mock_get_auth.return_value = mock_user_auth
    mock_user = MagicMock(linear_workspace_id=10)
    mock_manager.integration_store.get_user_by_active_workspace.return_value = mock_user
    mock_manager.integration_store.get_workspace_by_id.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        await get_current_workspace_link(mock_request)
    assert exc_info.value.status_code == 404
    assert 'Workspace not found for the user' in exc_info.value.detail


@pytest.mark.asyncio
@patch('server.routes.integration.linear.get_user_auth')
@patch('server.routes.integration.linear.linear_manager', new_callable=AsyncMock)
async def test_get_current_workspace_link_not_editable(
    mock_manager, mock_get_auth, mock_request, mock_user_auth
):
    mock_get_auth.return_value = mock_user_auth
    user_id = 'test_user_id'
    different_admin = 'different_admin'

    mock_user = MagicMock(
        id=1,
        keycloak_user_id=user_id,
        linear_workspace_id=10,
        status='active',
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    mock_workspace = MagicMock(
        id=10,
        status='active',
        admin_user_id=different_admin,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        linear_org_id='test-org-id',
        svc_acc_email='service@test.com',
        svc_acc_api_key='encrypted-key',
    )
    # Fix the name attribute to be a string instead of MagicMock
    mock_workspace.name = 'test-space'

    mock_manager.integration_store.get_user_by_active_workspace.return_value = mock_user
    mock_manager.integration_store.get_workspace_by_id.return_value = mock_workspace

    response = await get_current_workspace_link(mock_request)
    assert response.workspace.editable is False


@pytest.mark.asyncio
@patch('server.routes.integration.linear.get_user_auth')
@patch('server.routes.integration.linear.linear_manager', new_callable=AsyncMock)
async def test_get_current_workspace_link_unexpected_error(
    mock_manager, mock_get_auth, mock_request, mock_user_auth
):
    mock_get_auth.return_value = mock_user_auth
    mock_manager.integration_store.get_user_by_active_workspace.side_effect = Exception(
        'DB error'
    )

    with pytest.raises(HTTPException) as exc_info:
        await get_current_workspace_link(mock_request)
    assert exc_info.value.status_code == 500
    assert 'Failed to retrieve user' in exc_info.value.detail


# Test unlink_workspace error scenarios
@pytest.mark.asyncio
@patch('server.routes.integration.linear.get_user_auth')
@patch('server.routes.integration.linear.linear_manager', new_callable=AsyncMock)
async def test_unlink_workspace_user_not_found(
    mock_manager, mock_get_auth, mock_request, mock_user_auth
):
    mock_get_auth.return_value = mock_user_auth
    mock_manager.integration_store.get_user_by_active_workspace.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        await unlink_workspace(mock_request)
    assert exc_info.value.status_code == 404
    assert 'User is not registered for Linear integration' in exc_info.value.detail


@pytest.mark.asyncio
@patch('server.routes.integration.linear.get_user_auth')
@patch('server.routes.integration.linear.linear_manager', new_callable=AsyncMock)
async def test_unlink_workspace_workspace_not_found(
    mock_manager, mock_get_auth, mock_request, mock_user_auth
):
    mock_get_auth.return_value = mock_user_auth
    mock_user = MagicMock(linear_workspace_id=10)
    mock_manager.integration_store.get_user_by_active_workspace.return_value = mock_user
    mock_manager.integration_store.get_workspace_by_id.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        await unlink_workspace(mock_request)
    assert exc_info.value.status_code == 404
    assert 'Workspace not found for the user' in exc_info.value.detail


@pytest.mark.asyncio
@patch('server.routes.integration.linear.get_user_auth')
@patch('server.routes.integration.linear.linear_manager', new_callable=AsyncMock)
async def test_unlink_workspace_non_admin(
    mock_manager, mock_get_auth, mock_request, mock_user_auth
):
    mock_get_auth.return_value = mock_user_auth
    user_id = 'test_user_id'
    mock_user = MagicMock(linear_workspace_id=10)
    mock_workspace = MagicMock(id=10, admin_user_id='different_admin')
    mock_manager.integration_store.get_user_by_active_workspace.return_value = mock_user
    mock_manager.integration_store.get_workspace_by_id.return_value = mock_workspace

    response = await unlink_workspace(mock_request)
    content = json.loads(response.body)
    assert content['success'] is True
    mock_manager.integration_store.update_user_integration_status.assert_called_once_with(
        user_id, 'inactive'
    )


@pytest.mark.asyncio
@patch('server.routes.integration.linear.get_user_auth')
@patch('server.routes.integration.linear.linear_manager', new_callable=AsyncMock)
async def test_unlink_workspace_unexpected_error(
    mock_manager, mock_get_auth, mock_request, mock_user_auth
):
    mock_get_auth.return_value = mock_user_auth
    mock_manager.integration_store.get_user_by_active_workspace.side_effect = Exception(
        'DB error'
    )

    with pytest.raises(HTTPException) as exc_info:
        await unlink_workspace(mock_request)
    assert exc_info.value.status_code == 500
    assert 'Failed to unlink user' in exc_info.value.detail


# Test validate_workspace_integration error scenarios
@pytest.mark.asyncio
@patch('server.routes.integration.linear.get_user_auth')
async def test_validate_workspace_integration_invalid_name(
    mock_get_auth, mock_request, mock_user_auth
):
    mock_get_auth.return_value = mock_user_auth

    with pytest.raises(HTTPException) as exc_info:
        await validate_workspace_integration(mock_request, 'invalid workspace!')
    assert exc_info.value.status_code == 400
    assert (
        'workspace_name can only contain alphanumeric characters'
        in exc_info.value.detail
    )


@pytest.mark.asyncio
@patch('server.routes.integration.linear.get_user_auth')
async def test_validate_workspace_integration_no_email(
    mock_get_auth, mock_request, mock_user_auth
):
    mock_user_auth.get_user_email.return_value = None
    mock_get_auth.return_value = mock_user_auth

    with pytest.raises(HTTPException) as exc_info:
        await validate_workspace_integration(mock_request, 'test-workspace')
    assert exc_info.value.status_code == 400
    assert 'Unable to retrieve user email' in exc_info.value.detail


@pytest.mark.asyncio
@patch('server.routes.integration.linear.get_user_auth')
@patch('server.routes.integration.linear.linear_manager', new_callable=AsyncMock)
async def test_validate_workspace_integration_workspace_not_found(
    mock_manager, mock_get_auth, mock_request, mock_user_auth
):
    mock_get_auth.return_value = mock_user_auth
    mock_manager.integration_store.get_workspace_by_name.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        await validate_workspace_integration(mock_request, 'nonexistent-workspace')
    assert exc_info.value.status_code == 404
    assert (
        "Workspace with name 'nonexistent-workspace' not found" in exc_info.value.detail
    )


@pytest.mark.asyncio
@patch('server.routes.integration.linear.get_user_auth')
@patch('server.routes.integration.linear.linear_manager', new_callable=AsyncMock)
async def test_validate_workspace_integration_inactive_workspace(
    mock_manager, mock_get_auth, mock_request, mock_user_auth
):
    mock_get_auth.return_value = mock_user_auth
    mock_workspace = MagicMock(status='inactive')
    # Fix the name attribute to be a string instead of MagicMock
    mock_workspace.name = 'test-workspace'
    mock_manager.integration_store.get_workspace_by_name.return_value = mock_workspace

    with pytest.raises(HTTPException) as exc_info:
        await validate_workspace_integration(mock_request, 'test-workspace')
    assert exc_info.value.status_code == 404
    assert "Workspace 'test-workspace' is not active" in exc_info.value.detail


@pytest.mark.asyncio
@patch('server.routes.integration.linear.get_user_auth')
@patch('server.routes.integration.linear.linear_manager', new_callable=AsyncMock)
async def test_validate_workspace_integration_unexpected_error(
    mock_manager, mock_get_auth, mock_request, mock_user_auth
):
    mock_get_auth.return_value = mock_user_auth
    mock_manager.integration_store.get_workspace_by_name.side_effect = Exception(
        'DB error'
    )

    with pytest.raises(HTTPException) as exc_info:
        await validate_workspace_integration(mock_request, 'test-workspace')
    assert exc_info.value.status_code == 500
    assert 'Failed to validate workspace' in exc_info.value.detail


# Test helper functions
@pytest.mark.asyncio
@patch('server.routes.integration.linear.linear_manager', new_callable=AsyncMock)
async def test_handle_workspace_link_creation_workspace_not_found(mock_manager):
    mock_manager.integration_store.get_workspace_by_name.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        await _handle_workspace_link_creation(
            'user1', 'linear_user_123', 'nonexistent-workspace'
        )
    assert exc_info.value.status_code == 404
    assert 'Workspace "nonexistent-workspace" not found' in exc_info.value.detail


@pytest.mark.asyncio
@patch('server.routes.integration.linear.linear_manager', new_callable=AsyncMock)
async def test_handle_workspace_link_creation_inactive_workspace(mock_manager):
    mock_workspace = MagicMock(status='inactive')
    mock_manager.integration_store.get_workspace_by_name.return_value = mock_workspace

    with pytest.raises(HTTPException) as exc_info:
        await _handle_workspace_link_creation(
            'user1', 'linear_user_123', 'inactive-workspace'
        )
    assert exc_info.value.status_code == 400
    assert 'Workspace "inactive-workspace" is not active' in exc_info.value.detail


@pytest.mark.asyncio
@patch('server.routes.integration.linear.linear_manager', new_callable=AsyncMock)
async def test_handle_workspace_link_creation_already_linked_same_workspace(
    mock_manager,
):
    mock_workspace = MagicMock(id=1, status='active')
    mock_existing_user = MagicMock(linear_workspace_id=1)

    mock_manager.integration_store.get_workspace_by_name.return_value = mock_workspace
    mock_manager.integration_store.get_user_by_active_workspace.return_value = (
        mock_existing_user
    )

    # Should not raise exception and should not create new link
    await _handle_workspace_link_creation('user1', 'linear_user_123', 'test-workspace')

    mock_manager.integration_store.create_workspace_link.assert_not_called()
    mock_manager.integration_store.update_user_integration_status.assert_not_called()


@pytest.mark.asyncio
@patch('server.routes.integration.linear.linear_manager', new_callable=AsyncMock)
async def test_handle_workspace_link_creation_already_linked_different_workspace(
    mock_manager,
):
    mock_workspace = MagicMock(id=2, status='active')
    mock_existing_user = MagicMock(linear_workspace_id=1)  # Different workspace

    mock_manager.integration_store.get_workspace_by_name.return_value = mock_workspace
    mock_manager.integration_store.get_user_by_active_workspace.return_value = (
        mock_existing_user
    )

    with pytest.raises(HTTPException) as exc_info:
        await _handle_workspace_link_creation(
            'user1', 'linear_user_123', 'test-workspace'
        )
    assert exc_info.value.status_code == 400
    assert 'You already have an active workspace link' in exc_info.value.detail


@pytest.mark.asyncio
@patch('server.routes.integration.linear.linear_manager', new_callable=AsyncMock)
async def test_handle_workspace_link_creation_reactivate_existing_link(mock_manager):
    mock_workspace = MagicMock(id=1, status='active')
    mock_existing_link = MagicMock()

    mock_manager.integration_store.get_workspace_by_name.return_value = mock_workspace
    mock_manager.integration_store.get_user_by_active_workspace.return_value = None
    mock_manager.integration_store.get_user_by_keycloak_id_and_workspace.return_value = mock_existing_link

    await _handle_workspace_link_creation('user1', 'linear_user_123', 'test-workspace')

    mock_manager.integration_store.update_user_integration_status.assert_called_once_with(
        'user1', 'active'
    )
    mock_manager.integration_store.create_workspace_link.assert_not_called()


@pytest.mark.asyncio
@patch('server.routes.integration.linear.linear_manager', new_callable=AsyncMock)
async def test_handle_workspace_link_creation_create_new_link(mock_manager):
    mock_workspace = MagicMock(id=1, status='active')

    mock_manager.integration_store.get_workspace_by_name.return_value = mock_workspace
    mock_manager.integration_store.get_user_by_active_workspace.return_value = None
    mock_manager.integration_store.get_user_by_keycloak_id_and_workspace.return_value = None

    await _handle_workspace_link_creation('user1', 'linear_user_123', 'test-workspace')

    mock_manager.integration_store.create_workspace_link.assert_called_once_with(
        keycloak_user_id='user1',
        linear_user_id='linear_user_123',
        linear_workspace_id=1,
    )
    mock_manager.integration_store.update_user_integration_status.assert_not_called()


@pytest.mark.asyncio
@patch('server.routes.integration.linear.linear_manager', new_callable=AsyncMock)
async def test_validate_workspace_update_permissions_workspace_not_found(mock_manager):
    mock_manager.integration_store.get_workspace_by_name.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        await _validate_workspace_update_permissions('user1', 'nonexistent-workspace')
    assert exc_info.value.status_code == 404
    assert 'Workspace "nonexistent-workspace" not found' in exc_info.value.detail


@pytest.mark.asyncio
@patch('server.routes.integration.linear.linear_manager', new_callable=AsyncMock)
async def test_validate_workspace_update_permissions_not_admin(mock_manager):
    mock_workspace = MagicMock(admin_user_id='different_user')
    mock_manager.integration_store.get_workspace_by_name.return_value = mock_workspace

    with pytest.raises(HTTPException) as exc_info:
        await _validate_workspace_update_permissions('user1', 'test-workspace')
    assert exc_info.value.status_code == 403
    assert (
        'You do not have permission to update this workspace' in exc_info.value.detail
    )


@pytest.mark.asyncio
@patch('server.routes.integration.linear.linear_manager', new_callable=AsyncMock)
async def test_validate_workspace_update_permissions_wrong_linked_workspace(
    mock_manager,
):
    mock_workspace = MagicMock(id=1, admin_user_id='user1')
    mock_user_link = MagicMock(linear_workspace_id=2)  # Different workspace

    mock_manager.integration_store.get_workspace_by_name.return_value = mock_workspace
    mock_manager.integration_store.get_user_by_active_workspace.return_value = (
        mock_user_link
    )

    with pytest.raises(HTTPException) as exc_info:
        await _validate_workspace_update_permissions('user1', 'test-workspace')
    assert exc_info.value.status_code == 403
    assert (
        'You can only update the workspace you are currently linked to'
        in exc_info.value.detail
    )


@pytest.mark.asyncio
@patch('server.routes.integration.linear.linear_manager', new_callable=AsyncMock)
async def test_validate_workspace_update_permissions_success(mock_manager):
    mock_workspace = MagicMock(id=1, admin_user_id='user1')
    mock_user_link = MagicMock(linear_workspace_id=1)

    mock_manager.integration_store.get_workspace_by_name.return_value = mock_workspace
    mock_manager.integration_store.get_user_by_active_workspace.return_value = (
        mock_user_link
    )

    result = await _validate_workspace_update_permissions('user1', 'test-workspace')
    assert result == mock_workspace


@pytest.mark.asyncio
@patch('server.routes.integration.linear.linear_manager', new_callable=AsyncMock)
async def test_validate_workspace_update_permissions_no_current_link(mock_manager):
    mock_workspace = MagicMock(id=1, admin_user_id='user1')

    mock_manager.integration_store.get_workspace_by_name.return_value = mock_workspace
    mock_manager.integration_store.get_user_by_active_workspace.return_value = None

    result = await _validate_workspace_update_permissions('user1', 'test-workspace')
    assert result == mock_workspace
