"""Test that third-party runtimes have been properly removed from the codebase."""

import pytest

from openhands.runtime import get_runtime_cls


def test_third_party_runtimes_not_available():
    """Test that third-party runtimes are no longer available in the runtime registry."""
    third_party_runtimes = ['daytona', 'modal', 'e2b', 'runloop']

    for runtime_name in third_party_runtimes:
        with pytest.raises(ValueError, match=f'Runtime {runtime_name} not supported'):
            get_runtime_cls(runtime_name)


def test_third_party_runtime_imports_fail():
    """Test that importing third-party runtime classes fails."""
    third_party_imports = [
        'openhands.runtime.impl.daytona.daytona_runtime.DaytonaRuntime',
        'openhands.runtime.impl.modal.modal_runtime.ModalRuntime',
        'openhands.runtime.impl.e2b.e2b_runtime.E2BRuntime',
        'openhands.runtime.impl.runloop.runloop_runtime.RunloopRuntime',
    ]

    for import_path in third_party_imports:
        module_path, class_name = import_path.rsplit('.', 1)
        with pytest.raises(ImportError):
            __import__(module_path, fromlist=[class_name])


def test_third_party_runtime_classes_not_in_runtime_init():
    """Test that third-party runtime classes are not exported from runtime.__init__."""
    from openhands import runtime

    third_party_classes = [
        'DaytonaRuntime',
        'ModalRuntime',
        'E2BRuntime',
        'RunloopRuntime',
    ]

    for class_name in third_party_classes:
        assert not hasattr(runtime, class_name), (
            f'{class_name} should not be available in runtime module'
        )


def test_available_runtimes_only_include_core_runtimes():
    """Test that only core runtimes are available."""
    from openhands.runtime import _DEFAULT_RUNTIME_CLASSES

    # These are the core runtimes that should remain
    expected_runtimes = {'eventstream', 'docker', 'remote', 'local', 'cli'}

    # Third-party runtimes that should be removed
    removed_runtimes = {'daytona', 'modal', 'e2b', 'runloop'}

    available_runtimes = set(_DEFAULT_RUNTIME_CLASSES.keys())

    # Check that core runtimes are still available
    for runtime in expected_runtimes:
        assert runtime in available_runtimes, (
            f'Core runtime {runtime} should still be available'
        )

    # Check that third-party runtimes are removed
    for runtime in removed_runtimes:
        assert runtime not in available_runtimes, (
            f'Third-party runtime {runtime} should be removed'
        )


def test_third_party_config_fields_removed():
    """Test that third-party runtime configuration fields have been removed."""
    from openhands.core.config.openhands_config import OpenHandsConfig

    config = OpenHandsConfig()

    # These fields should be removed
    removed_fields = [
        'e2b_api_key',
        'modal_api_token_id',
        'modal_api_token_secret',
        'runloop_api_key',
        'daytona_api_key',
        'daytona_api_url',
        'daytona_target',
    ]

    for field in removed_fields:
        assert not hasattr(config, field), (
            f'Configuration field {field} should be removed'
        )
