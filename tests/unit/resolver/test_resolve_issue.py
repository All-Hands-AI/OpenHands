import os
from unittest import mock

import pytest

from openhands.core.config import SandboxConfig
from openhands.resolver.resolve_issue import IssueResolver
import openhands

def assert_sandbox_config(
    config: SandboxConfig,
    base_container_image = SandboxConfig.model_fields["base_container_image"].default,
    runtime_container_image = f'ghcr.io/all-hands-ai/runtime:mock-nikolaik',  # Default to mock version
    local_runtime_url = SandboxConfig.model_fields["local_runtime_url"].default,
):
    """Helper function to assert the properties of the SandboxConfig object."""
    assert isinstance(config, SandboxConfig)
    assert config.base_container_image == base_container_image
    assert config.runtime_container_image == runtime_container_image
    assert config.enable_auto_lint is False
    assert config.use_host_network is False
    assert config.timeout == 300
    assert config.local_runtime_url == local_runtime_url

def test_setup_sandbox_config_default():
    """Test default configuration when no images provided and not experimental"""
    with mock.patch('openhands.__version__', 'mock'):
        config = IssueResolver._setup_sandbox_config(
            base_container_image=None,
            runtime_container_image=None,
            is_experimental=False,
        )

        assert_sandbox_config(
            config,
            runtime_container_image='ghcr.io/all-hands-ai/runtime:mock-nikolaik'
        )


def test_setup_sandbox_config_both_images():
    """Test that providing both container images raises ValueError"""
    with pytest.raises(ValueError, match="Cannot provide both runtime and base container images."):
        IssueResolver._setup_sandbox_config(
            base_container_image="base-image",
            runtime_container_image="runtime-image",
            is_experimental=False,
        )

def test_setup_sandbox_config_base_only():
    """Test configuration when only base_container_image is provided"""
    base_image = "custom-base-image"
    config = IssueResolver._setup_sandbox_config(
        base_container_image=base_image,
        runtime_container_image=None,
        is_experimental=False,
    )

    assert_sandbox_config(
        config,
        base_container_image=base_image,
        runtime_container_image=None
    )

def test_setup_sandbox_config_runtime_only():
    """Test configuration when only runtime_container_image is provided"""
    runtime_image = "custom-runtime-image"
    config = IssueResolver._setup_sandbox_config(
        base_container_image=None,
        runtime_container_image=runtime_image,
        is_experimental=False,
    )

    assert_sandbox_config(
        config,
        runtime_container_image=runtime_image
    )
 
def test_setup_sandbox_config_experimental():
    """Test configuration when experimental mode is enabled"""
    with mock.patch('openhands.__version__', 'mock'):
        config = IssueResolver._setup_sandbox_config(
            base_container_image=None,
            runtime_container_image=None,
            is_experimental=True,
        )

        assert_sandbox_config(
            config,
            runtime_container_image=None
        )

@mock.patch("openhands.resolver.resolve_issue.os.getuid", return_value=0)
@mock.patch("openhands.resolver.resolve_issue.get_unique_uid", return_value=1001)
def test_setup_sandbox_config_gitlab_ci(mock_get_unique_uid, mock_getuid):
    """Test GitLab CI specific configuration when running as root"""
    with mock.patch('openhands.__version__', 'mock'):
        with mock.patch.object(IssueResolver, "GITLAB_CI", True):
            config = IssueResolver._setup_sandbox_config(
                base_container_image=None,
                runtime_container_image=None,
                is_experimental=False,
            )
            
            assert_sandbox_config(
                config,
                local_runtime_url="http://localhost"
            )

@mock.patch("openhands.resolver.resolve_issue.os.getuid", return_value=1000)
def test_setup_sandbox_config_gitlab_ci_non_root(mock_getuid):
    """Test GitLab CI configuration when not running as root"""
    with mock.patch('openhands.__version__', 'mock'):
        with mock.patch.object(IssueResolver, "GITLAB_CI", True):
            config = IssueResolver._setup_sandbox_config(
                base_container_image=None,
                runtime_container_image=None,
                is_experimental=False,
            )

            assert_sandbox_config(
                config,
                local_runtime_url="http://localhost"
            )