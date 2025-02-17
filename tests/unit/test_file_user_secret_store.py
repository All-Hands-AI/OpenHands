import json
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from pydantic import SecretStr

from openhands.core.config.app_config import AppConfig
from openhands.storage.data_models.token_factory import ApiKey
from openhands.storage.data_models.user_secret import UserSecret
from openhands.storage.files import FileStore
from openhands.storage.user_secret.file_user_secret_store import FileUserSecretStore


@pytest.fixture
def mock_file_store():
    return MagicMock(spec=FileStore)


@pytest.fixture
def file_user_secret_store(mock_file_store):
    return FileUserSecretStore(
        file_store=mock_file_store,
        jwt_secret=SecretStr('test-jwt-secret'),
        path='secrets/',
    )


@pytest.fixture
def sample_secret():
    return UserSecret(
        id='test-id',
        key='api-key',
        user_id='user-123',
        token_factory=ApiKey(secret_value=SecretStr('test-secret-value')),
        updated_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
    )


@pytest.mark.asyncio
async def test_load_nonexistent_secret(file_user_secret_store):
    file_user_secret_store.file_store.read.side_effect = FileNotFoundError()
    assert await file_user_secret_store.load_secret('nonexistent-id') is None


@pytest.mark.asyncio
async def test_save_and_load_secret(file_user_secret_store, sample_secret):
    # Save the secret
    await file_user_secret_store.save_secret(sample_secret)

    # Get the saved data from the mock
    saved_data = json.loads(file_user_secret_store.file_store.write.call_args[0][1])

    # Setup mock for load with the saved data
    file_user_secret_store.file_store.read.return_value = json.dumps(saved_data)

    # Load and verify
    loaded_secret = await file_user_secret_store.load_secret(sample_secret.id)
    assert loaded_secret is not None
    assert loaded_secret.id == sample_secret.id
    assert loaded_secret.key == sample_secret.key
    assert loaded_secret.user_id == sample_secret.user_id
    assert loaded_secret.token_factory == sample_secret.token_factory
    assert isinstance(loaded_secret.updated_at, datetime)
    assert isinstance(loaded_secret.created_at, datetime)


@pytest.mark.asyncio
async def test_delete_secret(file_user_secret_store):
    # Test successful deletion
    assert await file_user_secret_store.delete_secret('existing-id') is True
    file_user_secret_store.file_store.delete.assert_called_once_with(
        'secrets/existing-id.json'
    )

    # Test deletion of non-existent secret
    file_user_secret_store.file_store.delete.side_effect = FileNotFoundError()
    assert await file_user_secret_store.delete_secret('nonexistent-id') is False


@pytest.mark.asyncio
async def test_search_secrets(file_user_secret_store, sample_secret):
    # Setup mock for list
    file_user_secret_store.file_store.list.return_value = ['secrets/test-id.json']

    # Save a secret to get proper encrypted data
    await file_user_secret_store.save_secret(sample_secret)
    saved_data = json.loads(file_user_secret_store.file_store.write.call_args[0][1])

    # Setup mock for read with the saved data
    file_user_secret_store.file_store.read.return_value = json.dumps(saved_data)

    # Test search with default parameters
    result_set = await file_user_secret_store.search()
    assert len(result_set.results) == 1
    assert result_set.results[0].id == sample_secret.id
    assert result_set.results[0].token_factory == sample_secret.token_factory
    assert isinstance(result_set.results[0].updated_at, datetime)
    assert isinstance(result_set.results[0].created_at, datetime)

    # Test empty search results
    file_user_secret_store.file_store.list.side_effect = FileNotFoundError()
    empty_result_set = await file_user_secret_store.search()
    assert len(empty_result_set.results) == 0


@pytest.mark.asyncio
async def test_get_instance():
    config = AppConfig(
        file_store='local',
        file_store_path='/test/path',
        jwt_secret=SecretStr('test-jwt-secret'),
    )

    with patch(
        'openhands.storage.user_secret.file_user_secret_store.get_file_store'
    ) as mock_get_store:
        mock_store = MagicMock(spec=FileStore)
        mock_get_store.return_value = mock_store

        store = await FileUserSecretStore.get_instance(config, 'user-123')

        assert isinstance(store, FileUserSecretStore)
        assert store.file_store == mock_store
        assert store.jwt_secret == config.jwt_secret
        mock_get_store.assert_called_once_with('local', '/test/path')


@pytest.mark.asyncio
async def test_encryption_decryption(file_user_secret_store):
    original_value = {'type': 'ApiKey', 'secret_value': 'test-secret-value'}
    encrypted = file_user_secret_store._encrypt_value(original_value)
    decrypted = file_user_secret_store._decrypt_value(encrypted)
    assert decrypted == original_value
