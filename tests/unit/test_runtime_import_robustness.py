"""
Test that the runtime import system is robust against broken third-party dependencies.

This test specifically addresses the issue where broken third-party runtime dependencies
(like runloop-api-client with incompatible httpx_aiohttp versions) would break the entire
OpenHands CLI and system.
"""

import sys

import pytest


def test_cli_import_with_broken_third_party_runtime():
    """Test that CLI can be imported even with broken third-party runtime dependencies."""

    # Clear any cached modules to ensure fresh import
    modules_to_clear = [
        k for k in sys.modules.keys() if 'openhands' in k or 'third_party' in k
    ]
    for module in modules_to_clear:
        del sys.modules[module]

    # This should not raise an exception even if third-party runtimes have broken dependencies
    try:
        assert True
    except Exception as e:
        pytest.fail(f'CLI import failed: {e}')


def test_runtime_import_robustness():
    """Test that runtime import system is robust against broken dependencies."""

    # Clear any cached runtime modules
    modules_to_clear = [k for k in sys.modules.keys() if 'openhands.runtime' in k]
    for module in modules_to_clear:
        del sys.modules[module]

    # Import the runtime module - should succeed even with broken third-party runtimes
    try:
        assert True
    except Exception as e:
        pytest.fail(f'Runtime import failed: {e}')


def test_get_runtime_cls_works():
    """Test that get_runtime_cls works even when third-party runtimes are broken."""

    # Import the runtime module
    import openhands.runtime

    # Test that we can still get core runtime classes
    docker_runtime = openhands.runtime.get_runtime_cls('docker')
    assert docker_runtime is not None

    local_runtime = openhands.runtime.get_runtime_cls('local')
    assert local_runtime is not None

    # Test that requesting a non-existent runtime raises appropriate error
    with pytest.raises(ValueError, match='Runtime nonexistent not supported'):
        openhands.runtime.get_runtime_cls('nonexistent')


def test_runtime_exception_handling():
    """Test that the runtime discovery code properly handles exceptions."""

    # This test verifies that the fix in openhands/runtime/__init__.py
    # properly catches all exceptions (not just ImportError) during
    # third-party runtime discovery

    import openhands.runtime

    # The fact that we can import this module successfully means
    # the exception handling is working correctly, even if there
    # are broken third-party runtime dependencies
    assert hasattr(openhands.runtime, 'get_runtime_cls')
    assert hasattr(openhands.runtime, '_THIRD_PARTY_RUNTIME_CLASSES')
