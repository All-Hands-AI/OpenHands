from unittest.mock import MagicMock, patch

import pytest

from openhands.core.config.openhands_config import OpenHandsConfig
from openhands.storage.data_models.settings import Settings
from openhands.storage.files import FileStore
from openhands.storage.settings.file_settings_store import FileSettingsStore


@pytest.fixture
def mock_file_store():
    return MagicMock(spec=FileStore)


@pytest.fixture
def file_settings_store(mock_file_store):
    return FileSettingsStore(mock_file_store)


@pytest.mark.asyncio
async def test_load_nonexistent_data(file_settings_store):
    with patch(
        'openhands.storage.data_models.settings.load_openhands_config',
        MagicMock(return_value=OpenHandsConfig()),
    ):
        file_settings_store.file_store.read.side_effect = FileNotFoundError()
        assert await file_settings_store.load() is None


@pytest.mark.asyncio
async def test_store_and_load_data(file_settings_store):
    # Test data
    init_data = Settings(
        language='python',
        agent='test-agent',
        max_iterations=100,
        security_analyzer='default',
        confirmation_mode=True,
        llm_model='test-model',
        llm_api_key='test-key',
        llm_base_url='https://test.com',
    )

    # Store data
    await file_settings_store.store(init_data)

    # Verify store called with correct JSON
    expected_json = init_data.model_dump_json(context={'expose_secrets': True})
    file_settings_store.file_store.write.assert_called_once_with(
        'settings.json', expected_json
    )

    # Setup mock for load
    file_settings_store.file_store.read.return_value = expected_json

    # Load and verify data
    loaded_data = await file_settings_store.load()
    assert loaded_data is not None
    assert loaded_data.language == init_data.language
    assert loaded_data.agent == init_data.agent
    assert loaded_data.max_iterations == init_data.max_iterations
    assert loaded_data.security_analyzer == init_data.security_analyzer
    assert loaded_data.confirmation_mode == init_data.confirmation_mode
    assert loaded_data.llm_model == init_data.llm_model
    assert loaded_data.llm_api_key
    assert init_data.llm_api_key
    assert (
        loaded_data.llm_api_key.get_secret_value()
        == init_data.llm_api_key.get_secret_value()
    )
    assert loaded_data.llm_base_url == init_data.llm_base_url


@pytest.mark.asyncio
async def test_get_instance():
    config = OpenHandsConfig(file_store='local', file_store_path='/test/path')

    with patch(
        'openhands.storage.settings.file_settings_store.get_file_store'
    ) as mock_get_store:
        mock_store = MagicMock(spec=FileStore)
        mock_get_store.return_value = mock_store

        store = await FileSettingsStore.get_instance(config, None)

        assert isinstance(store, FileSettingsStore)
        assert store.file_store == mock_store
        mock_get_store.assert_called_once_with('local', '/test/path', None, None)
