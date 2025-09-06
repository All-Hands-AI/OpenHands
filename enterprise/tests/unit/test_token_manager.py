from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session
from storage.offline_token_store import OfflineTokenStore
from storage.stored_offline_token import StoredOfflineToken

from openhands.core.config.openhands_config import OpenHandsConfig


@pytest.fixture
def mock_session():
    session = MagicMock(spec=Session)
    return session


@pytest.fixture
def mock_session_maker(mock_session):
    session_maker = MagicMock()
    session_maker.return_value.__enter__.return_value = mock_session
    session_maker.return_value.__exit__.return_value = None
    return session_maker


@pytest.fixture
def mock_config():
    return MagicMock(spec=OpenHandsConfig)


@pytest.fixture
def token_store(mock_session_maker, mock_config):
    return OfflineTokenStore('test_user_id', mock_session_maker, mock_config)


@pytest.mark.asyncio
async def test_store_token_new_record(token_store, mock_session):
    # Setup
    mock_session.query.return_value.filter.return_value.first.return_value = None
    test_token = 'test_offline_token'

    # Execute
    await token_store.store_token(test_token)

    # Verify
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()
    added_record = mock_session.add.call_args[0][0]
    assert isinstance(added_record, StoredOfflineToken)
    assert added_record.user_id == 'test_user_id'
    assert added_record.offline_token == test_token


@pytest.mark.asyncio
async def test_store_token_existing_record(token_store, mock_session):
    # Setup
    existing_record = StoredOfflineToken(
        user_id='test_user_id', offline_token='old_token'
    )
    mock_session.query.return_value.filter.return_value.first.return_value = (
        existing_record
    )
    test_token = 'new_offline_token'

    # Execute
    await token_store.store_token(test_token)

    # Verify
    mock_session.add.assert_not_called()
    mock_session.commit.assert_called_once()
    assert existing_record.offline_token == test_token


@pytest.mark.asyncio
async def test_load_token_existing(token_store, mock_session):
    # Setup
    test_token = 'test_offline_token'
    mock_session.query.return_value.filter.return_value.first.return_value = (
        StoredOfflineToken(user_id='test_user_id', offline_token=test_token)
    )

    # Execute
    result = await token_store.load_token()

    # Verify
    assert result == test_token


@pytest.mark.asyncio
async def test_load_token_not_found(token_store, mock_session):
    # Setup
    mock_session.query.return_value.filter.return_value.first.return_value = None

    # Execute
    result = await token_store.load_token()

    # Verify
    assert result is None


@pytest.mark.asyncio
async def test_get_instance(mock_config):
    # Setup
    test_user_id = 'test_user_id'

    # Execute
    result = await OfflineTokenStore.get_instance(mock_config, test_user_id)

    # Verify
    assert isinstance(result, OfflineTokenStore)
    assert result.user_id == test_user_id
    assert result.config == mock_config
