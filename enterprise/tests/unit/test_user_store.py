import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import SecretStr

# Mock the database module before importing UserStore
with patch('storage.database.engine'), patch('storage.database.a_engine'):
    from storage.user import User
    from storage.user_store import UserStore

from openhands.storage.data_models.settings import Settings


@pytest.fixture
def mock_litellm_api():
    api_key_patch = patch('storage.lite_llm_manager.LITE_LLM_API_KEY', 'test_key')
    api_url_patch = patch(
        'storage.lite_llm_manager.LITE_LLM_API_URL', 'http://test.url'
    )
    team_id_patch = patch('storage.lite_llm_manager.LITE_LLM_TEAM_ID', 'test_team')
    client_patch = patch('httpx.AsyncClient')

    with api_key_patch, api_url_patch, team_id_patch, client_patch as mock_client:
        mock_response = AsyncMock()
        mock_response.is_success = True
        mock_response.json = MagicMock(return_value={'key': 'test_api_key'})
        mock_client.return_value.__aenter__.return_value.post.return_value = (
            mock_response
        )
        mock_client.return_value.__aenter__.return_value.get.return_value = (
            mock_response
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


@pytest.mark.asyncio
async def test_create_default_settings_no_org_id():
    # Test UserStore.create_default_settings with empty org_id
    settings = await UserStore.create_default_settings('', 'test-user-id')
    assert settings is None


@pytest.mark.asyncio
async def test_create_default_settings_require_payment_enabled(
    session_maker, mock_stripe
):
    # Mock stripe_service.has_payment_method to return False
    with (
        patch('storage.user_store.REQUIRE_PAYMENT', True),
        patch(
            'stripe.Customer.list_payment_methods_async',
            AsyncMock(return_value=MagicMock(data=[])),
        ),
        patch('integrations.stripe_service.session_maker', session_maker),
    ):
        settings = await UserStore.create_default_settings(
            'test-org-id', 'test-user-id'
        )
        assert settings is None


@pytest.mark.asyncio
async def test_create_default_settings_require_payment_disabled(
    session_maker, mock_stripe, mock_litellm_api
):
    # Even without payment method, should get default settings when REQUIRE_PAYMENT is False
    with (
        patch('storage.user_store.REQUIRE_PAYMENT', False),
        patch(
            'stripe.Customer.list_payment_methods_async',
            AsyncMock(return_value=MagicMock(data=[])),
        ),
        patch('integrations.stripe_service.session_maker', session_maker),
        patch('storage.user_store.session_maker', session_maker),
        patch('storage.org_store.session_maker', session_maker),
        patch(
            'server.auth.token_manager.TokenManager.get_user_info_from_user_id',
            AsyncMock(return_value={'attributes': {'github_id': ['12345']}}),
        ),
    ):
        settings = await UserStore.create_default_settings(
            'test-org-id', 'test-user-id'
        )
        assert settings is not None
        assert settings.language == 'en'
        assert settings.enable_proactive_conversation_starters is True


@pytest.mark.asyncio
async def test_create_default_settings_with_litellm(session_maker, mock_litellm_api):
    # Test that UserStore.create_default_settings works with LiteLLM
    with (
        patch('storage.user_store.REQUIRE_PAYMENT', False),
        patch('integrations.stripe_service.session_maker', session_maker),
        patch('storage.user_store.session_maker', session_maker),
        patch('storage.org_store.session_maker', session_maker),
        patch(
            'server.auth.token_manager.TokenManager.get_user_info_from_user_id',
            AsyncMock(return_value={'attributes': {'github_id': ['12345']}}),
        ),
    ):
        settings = await UserStore.create_default_settings(
            'test-org-id', 'test-user-id'
        )
        assert settings is not None
        assert settings.llm_api_key.get_secret_value() == 'test_api_key'
        assert settings.llm_base_url == 'http://test.url'
        assert settings.agent == 'CodeActAgent'


@pytest.mark.skip(reason='Complex integration test with session isolation issues')
@pytest.mark.asyncio
async def test_create_user(session_maker, mock_litellm_api):
    # Test creating a new user - skipped due to complex session isolation issues
    pass


def test_get_user_by_keycloak_id(session_maker):
    # Test getting user by keycloak ID
    test_org_id = uuid.uuid4()
    with session_maker() as session:
        # Create a test user
        user = User(keycloak_user_id='test-id', current_org_id=test_org_id)
        session.add(user)
        session.commit()
        user_id = user.id

    # Test retrieval
    with patch('storage.user_store.session_maker', session_maker):
        retrieved_user = UserStore.get_user_by_keycloak_id('test-id')
        assert retrieved_user is not None
        assert retrieved_user.id == user_id
        assert retrieved_user.keycloak_user_id == 'test-id'


def test_get_user_by_id(session_maker):
    # Test getting user by ID
    test_org_id = uuid.uuid4()
    with session_maker() as session:
        # Create a test user
        user = User(keycloak_user_id='test-id', current_org_id=test_org_id)
        session.add(user)
        session.commit()
        user_id = user.id

    # Test retrieval
    with patch('storage.user_store.session_maker', session_maker):
        retrieved_user = UserStore.get_user_by_id(user_id)
        assert retrieved_user is not None
        assert retrieved_user.id == user_id
        assert retrieved_user.keycloak_user_id == 'test-id'


def test_update_user(session_maker):
    # Test updating user details
    test_org_id1 = uuid.uuid4()
    test_org_id2 = uuid.uuid4()
    with session_maker() as session:
        # Create a test user
        user = User(keycloak_user_id='test-id', current_org_id=test_org_id1)
        session.add(user)
        session.commit()
        user_id = user.id

    # Test update
    with patch('storage.user_store.session_maker', session_maker):
        updated_user = UserStore.update_user(
            user_id=user_id,
            current_org_id=test_org_id2,
            role_id=3,
            enable_sound_notifications=True,
        )

        assert updated_user is not None
        assert updated_user.current_org_id == test_org_id2
        assert updated_user.role_id == 3
        assert updated_user.enable_sound_notifications is True


def test_list_users(session_maker):
    # Test listing all users
    test_org_id1 = uuid.uuid4()
    test_org_id2 = uuid.uuid4()
    with session_maker() as session:
        # Create test users
        user1 = User(keycloak_user_id='test-id-1', current_org_id=test_org_id1)
        user2 = User(keycloak_user_id='test-id-2', current_org_id=test_org_id2)
        session.add_all([user1, user2])
        session.commit()

    # Test listing
    with patch('storage.user_store.session_maker', session_maker):
        users = UserStore.list_users()
        assert len(users) >= 2
        keycloak_ids = [user.keycloak_user_id for user in users]
        assert 'test-id-1' in keycloak_ids
        assert 'test-id-2' in keycloak_ids


def test_get_kwargs_from_settings():
    # Test extracting user kwargs from settings
    settings = Settings(
        language='es',
        enable_sound_notifications=True,
        llm_api_key=SecretStr('test-key'),
    )

    kwargs = UserStore.get_kwargs_from_settings(settings)

    # Should only include fields that exist in User model
    assert 'language' in kwargs
    assert 'enable_sound_notifications' in kwargs
    # Should not include fields that don't exist in User model
    assert 'llm_api_key' not in kwargs
