from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import SecretStr
from server.constants import (
    CURRENT_USER_SETTINGS_VERSION,
    LITE_LLM_API_URL,
    LITE_LLM_TEAM_ID,
)
from storage.saas_settings_store import SaasSettingsStore
from storage.user_settings import UserSettings

from openhands.core.config.openhands_config import OpenHandsConfig
from openhands.server.settings import Settings


@pytest.fixture
def mock_litellm_get_response():
    mock_response = AsyncMock()
    mock_response.is_success = True
    mock_response.json = MagicMock(return_value={'user_info': {}})
    return mock_response


@pytest.fixture
def mock_litellm_post_response():
    mock_response = AsyncMock()
    mock_response.is_success = True
    mock_response.json = MagicMock(return_value={'key': 'test_api_key'})
    return mock_response


@pytest.fixture
def mock_litellm_api(mock_litellm_get_response, mock_litellm_post_response):
    api_key_patch = patch('storage.saas_settings_store.LITE_LLM_API_KEY', 'test_key')
    api_url_patch = patch(
        'storage.saas_settings_store.LITE_LLM_API_URL', 'http://test.url'
    )
    team_id_patch = patch('storage.saas_settings_store.LITE_LLM_TEAM_ID', 'test_team')
    client_patch = patch('httpx.AsyncClient')

    with api_key_patch, api_url_patch, team_id_patch, client_patch as mock_client:
        mock_client.return_value.__aenter__.return_value.get.return_value = (
            mock_litellm_get_response
        )
        mock_client.return_value.__aenter__.return_value.post.return_value = (
            mock_litellm_post_response
        )
        yield mock_client


@pytest.fixture
def mock_stripe():
    search_patch = patch(
        'stripe.Customer.search_async',
        AsyncMock(return_value=MagicMock(id='mock-customer-id')),
    )
    payment_patch = patch(
        'stripe.Customer.list_payment_methods_async',
        AsyncMock(return_value=MagicMock(data=[{}])),
    )
    with search_patch, payment_patch:
        yield


@pytest.fixture
def mock_github_user():
    with patch(
        'server.auth.token_manager.TokenManager.get_user_info_from_user_id',
        AsyncMock(return_value={'attributes': {'github_id': ['12345']}}),
    ) as mock_github:
        yield mock_github


@pytest.fixture
def mock_config():
    config = MagicMock(spec=OpenHandsConfig)
    config.jwt_secret = SecretStr('test_secret')
    config.file_store = 'google_cloud'
    config.file_store_path = 'bucket'
    return config


@pytest.fixture
def settings_store(session_maker, mock_config):
    store = SaasSettingsStore('user-id', session_maker, mock_config)

    # Patch the store method directly to filter out email and email_verified
    original_load = store.load

    # Patch the load method to add email and email_verified
    async def patched_load():
        settings = await original_load()
        if settings:
            # Add email and email_verified fields to mimic SaasUserAuth behavior
            settings.email = 'test@example.com'
            settings.email_verified = True
        return settings


    # Patch the store method to filter out email and email_verified
    async def patched_store(item):
        if item:
            # Make a copy of the item without email and email_verified
            item_dict = item.model_dump(context={'expose_secrets': True})
            if 'email' in item_dict:
                del item_dict['email']
            if 'email_verified' in item_dict:
                del item_dict['email_verified']
            if 'secrets_store' in item_dict:
                del item_dict['secrets_store']

            # Continue with the original implementation
            with store.session_maker() as session:
                existing = None
                if item_dict:
                    store._encrypt_kwargs(item_dict)
                    query = session.query(UserSettings).filter(
                        UserSettings.keycloak_user_id == store.user_id
                    )

                    # First check if we have an existing entry in the new table
                    existing = query.first()

                if existing:
                    # Update existing entry
                    for key, value in item_dict.items():
                        if key in existing.__class__.__table__.columns:
                            setattr(existing, key, value)
                    existing.user_version = CURRENT_USER_SETTINGS_VERSION
                    session.merge(existing)
                else:
                    item_dict['keycloak_user_id'] = store.user_id
                    item_dict['user_version'] = CURRENT_USER_SETTINGS_VERSION
                    settings = UserSettings(**item_dict)
                    session.add(settings)
                session.commit()

    # Replace the methods with our patched versions
    store.store = patched_store
    store.load = patched_load
    return store


@pytest.mark.asyncio
async def test_store_and_load_keycloak_user(settings_store):
    # Set a UUID-like Keycloak user ID
    settings_store.user_id = '550e8400-e29b-41d4-a716-446655440000'
    settings = Settings(
        llm_api_key=SecretStr('secret_key'),
        llm_base_url=LITE_LLM_API_URL,
        agent='smith',
        email='test@example.com',
        email_verified=True,
    )

    await settings_store.store(settings)

    # Load and verify settings
    loaded_settings = await settings_store.load()
    assert loaded_settings is not None
    assert loaded_settings.llm_api_key.get_secret_value() == 'secret_key'
    assert loaded_settings.agent == 'smith'

    # Verify it was stored in user_settings table with keycloak_user_id
    with settings_store.session_maker() as session:
        stored = (
            session.query(UserSettings)
            .filter(
                UserSettings.keycloak_user_id == '550e8400-e29b-41d4-a716-446655440000'
            )
            .first()
        )
        assert stored is not None
        assert stored.agent == 'smith'


@pytest.mark.asyncio
async def test_load_returns_default_when_not_found(
    settings_store, mock_litellm_api, mock_stripe, mock_github_user, session_maker
):
    file_store = MagicMock()
    file_store.read.side_effect = FileNotFoundError()

    with (
        patch(
            'storage.saas_settings_store.get_file_store',
            MagicMock(return_value=file_store),
        ),
        patch('storage.saas_settings_store.session_maker', session_maker),
    ):
        loaded_settings = await settings_store.load()
        assert loaded_settings is not None
        assert loaded_settings.language == 'en'
        assert loaded_settings.agent == 'CodeActAgent'
        assert loaded_settings.llm_api_key.get_secret_value() == 'test_api_key'
        assert loaded_settings.llm_base_url == 'http://test.url'


@pytest.mark.asyncio
async def test_create_user_in_lite_llm(settings_store):
    # Test the _create_user_in_lite_llm method directly
    mock_client = AsyncMock()
    mock_response = AsyncMock()
    mock_response.is_success = True
    mock_client.post.return_value = mock_response

    # Test with email
    await settings_store._create_user_in_lite_llm(
        mock_client, 'test@example.com', 50, 10
    )

    # Get the actual call arguments
    call_args = mock_client.post.call_args[1]

    # Check that the URL and most of the JSON payload match what we expect
    assert call_args['json']['user_email'] == 'test@example.com'
    assert call_args['json']['models'] == []
    assert call_args['json']['max_budget'] == 50
    assert call_args['json']['spend'] == 10
    assert call_args['json']['user_id'] == 'user-id'
    assert call_args['json']['teams'] == [LITE_LLM_TEAM_ID]
    assert call_args['json']['auto_create_key'] is True
    assert call_args['json']['send_invite_email'] is False
    assert call_args['json']['metadata']['version'] == CURRENT_USER_SETTINGS_VERSION
    assert 'model' in call_args['json']['metadata']

    # Test with None email
    mock_client.post.reset_mock()
    await settings_store._create_user_in_lite_llm(mock_client, None, 25, 15)

    # Get the actual call arguments
    call_args = mock_client.post.call_args[1]

    # Check that the URL and most of the JSON payload match what we expect
    assert call_args['json']['user_email'] is None
    assert call_args['json']['models'] == []
    assert call_args['json']['max_budget'] == 25
    assert call_args['json']['spend'] == 15
    assert call_args['json']['user_id'] == str(settings_store.user_id)
    assert call_args['json']['teams'] == [LITE_LLM_TEAM_ID]
    assert call_args['json']['auto_create_key'] is True
    assert call_args['json']['send_invite_email'] is False
    assert call_args['json']['metadata']['version'] == CURRENT_USER_SETTINGS_VERSION
    assert 'model' in call_args['json']['metadata']

    # Verify response is returned correctly
    assert (
        await settings_store._create_user_in_lite_llm(
            mock_client, 'email@test.com', 30, 7
        )
        == mock_response
    )


@pytest.mark.asyncio
async def test_encryption(settings_store):
    settings_store.user_id = 'mock-id'  # GitHub user ID
    settings = Settings(
        llm_api_key=SecretStr('secret_key'),
        agent='smith',
        llm_base_url=LITE_LLM_API_URL,
        email='test@example.com',
        email_verified=True,
    )
    await settings_store.store(settings)
    with settings_store.session_maker() as session:
        stored = (
            session.query(UserSettings)
            .filter(UserSettings.keycloak_user_id == 'mock-id')
            .first()
        )
        # The stored key should be encrypted
        assert stored.llm_api_key != 'secret_key'
        # But we should be able to decrypt it when loading
        loaded_settings = await settings_store.load()
        assert loaded_settings.llm_api_key.get_secret_value() == 'secret_key'
