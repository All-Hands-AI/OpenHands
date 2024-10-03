from unittest.mock import patch

import pytest

from openhands.runtime import (
    RuntimeInfo,
    _registered_runtimes,
    get_runtime_cls,
    register_runtime,
)


def test_register_and_get_runtime():
    # Register a new runtime
    register_runtime('test_runtime', 'test_module', 'TestRuntime')

    # Check if it's registered
    assert 'test_runtime' in _registered_runtimes
    assert _registered_runtimes['test_runtime'] == RuntimeInfo(
        'test_module', 'TestRuntime'
    )

    # Mock the import process
    with patch('importlib.import_module') as mock_import:
        mock_module = mock_import.return_value
        mock_module.TestRuntime = 'mock_runtime_class'  # Mock the runtime class

        # Get the runtime class
        runtime_cls = get_runtime_cls('test_runtime')

        # Check if the correct module was imported
        mock_import.assert_called_once_with('openhands.runtime.test_module.runtime')

        # Check if the correct class was returned
        assert runtime_cls == 'mock_runtime_class'


def test_get_runtime_not_found():
    with pytest.raises(ValueError, match='Runtime unknown_runtime not supported'):
        get_runtime_cls('unknown_runtime')
