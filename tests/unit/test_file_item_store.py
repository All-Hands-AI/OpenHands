import json
from unittest.mock import MagicMock, patch
from dataclasses import dataclass

import pytest

from openhands.storage.file_item_store import FileItemStore
from openhands.storage.files import FileStore


@dataclass
class TestItem:
    name: str
    value: int


def test_load_existing_item():
    # Arrange
    mock_file_store = MagicMock(spec=FileStore)
    test_json = '{"name": "test", "value": 42}'
    mock_file_store.read.return_value = test_json
    
    store = FileItemStore(
        type=TestItem,
        files=mock_file_store,
        pattern='test/{id}.json'
    )

    # Act
    item = store.load('test_id')

    # Assert
    assert isinstance(item, TestItem)
    assert item.name == 'test'
    assert item.value == 42
    mock_file_store.read.assert_called_once_with('test/test_id.json')


def test_load_nonexistent_item():
    # Arrange
    mock_file_store = MagicMock(spec=FileStore)
    mock_file_store.read.side_effect = FileNotFoundError()
    
    store = FileItemStore(
        type=TestItem,
        files=mock_file_store,
        pattern='test/{id}.json'
    )

    # Act
    item = store.load('nonexistent_id')

    # Assert
    assert item is None
    mock_file_store.read.assert_called_once_with('test/nonexistent_id.json')


def test_load_invalid_json():
    # Arrange
    mock_file_store = MagicMock(spec=FileStore)
    mock_file_store.read.return_value = 'invalid json'
    
    store = FileItemStore(
        type=TestItem,
        files=mock_file_store,
        pattern='test/{id}.json'
    )

    # Act & Assert
    with pytest.raises(json.JSONDecodeError):
        store.load('test_id')


def test_store_item():
    # Arrange
    mock_file_store = MagicMock(spec=FileStore)
    test_item = TestItem(name='test', value=42)
    
    store = FileItemStore(
        type=TestItem,
        files=mock_file_store,
        pattern='test/{id}.json'
    )

    # Act
    store.store('test_id', test_item)

    # Assert
    expected_json = '{"name": "test", "value": 42}'
    mock_file_store.write.assert_called_once_with(
        'test/test_id.json',
        expected_json
    )


def test_store_with_custom_pattern():
    # Arrange
    mock_file_store = MagicMock(spec=FileStore)
    test_item = TestItem(name='test', value=42)
    
    store = FileItemStore(
        type=TestItem,
        files=mock_file_store,
        pattern='custom/path/{id}/data.json'
    )

    # Act
    store.store('test_id', test_item)

    # Assert
    mock_file_store.write.assert_called_once_with(
        'custom/path/test_id/data.json',
        '{"name": "test", "value": 42}'
    )