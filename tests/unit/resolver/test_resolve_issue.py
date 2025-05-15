import os
from unittest import mock

import pytest

from openhands.core.config import SandboxConfig
from openhands.resolver.resolve_issue import setup_sandbox_config, SandboxContainerConfig
import openhands

def assert_sandbox_config(
    config: SandboxConfig,
    base_container_image = SandboxConfig.model_fields["base_container_image"].default,
    runtime_container_image = "ghcr.io/all-hands-ai/runtime:0.38.0-nikolaik",
    local_runtime_url = SandboxConfig.model_fields["local_runtime_url"].default,
    user_id = SandboxConfig.model_fields["user_id"].default,
):
    """Helper function to assert the properties of the SandboxConfig object."""
    assert isinstance(config, SandboxConfig)
    assert config.base_container_image == base_container_image
    assert config.runtime_container_image == runtime_container_image
    assert config.enable_auto_lint is False
    assert config.use_host_network is False
    assert config.timeout == 300
    assert config.local_runtime_url == local_runtime_url
    assert config.user_id == user_id

def test_setup_sandbox_config_default():
    """Test default configuration when no images provided and not experimental"""
    config = setup_sandbox_config(
        base_container_image=None,
        runtime_container_image=None,
        is_experimental=False,
    )

    assert_sandbox_config(config)

def test_setup_sandbox_config_both_images():
    """Test that providing both container images raises ValueError"""
    with pytest.raises(ValueError, match="Cannot provide both runtime and base container images."):
        setup_sandbox_config(
            base_container_image="base-image",
            runtime_container_image="runtime-image",
            is_experimental=False,
        )

def test_setup_sandbox_config_base_only():
    """Test configuration when only base_container_image is provided"""
    base_image = "custom-base-image"
    config = setup_sandbox_config(
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
    config = setup_sandbox_config(
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
    config = setup_sandbox_config(
        base_container_image=None,
        runtime_container_image=None,
        is_experimental=True,
    )

    assert_sandbox_config(
        config,
        runtime_container_image=None
    )

@mock.patch.dict("openhands.resolver.resolve_issue.os.environ", {"GITLAB_CI": "true"})
@mock.patch("openhands.resolver.resolve_issue.os.getuid", return_value=0)
@mock.patch("openhands.resolver.utils.get_unique_uid", return_value=1001)
def test_setup_sandbox_config_gitlab_ci(mock_get_unique_uid, mock_getuid):
    """Test GitLab CI specific configuration when running as root"""
    config = setup_sandbox_config(
        base_container_image=None,
        runtime_container_image=None,
        is_experimental=False,
    )
    
    assert_sandbox_config(
        config,
        local_runtime_url="http://localhost",
        user_id=1001
    )

@mock.patch.dict("openhands.resolver.resolve_issue.os.environ", {"GITLAB_CI": "true"})
@mock.patch("openhands.resolver.resolve_issue.os.getuid", return_value=1000)
def test_setup_sandbox_config_gitlab_ci_non_root(mock_getuid):
    """Test GitLab CI configuration when not running as root"""
    config = setup_sandbox_config(
        base_container_image=None,
        runtime_container_image=None,
        is_experimental=False,
    )

    assert_sandbox_config(
        config,
        local_runtime_url="http://localhost",
        user_id=1000
    )

# Additional tests for SandboxContainerConfig

def test_sandbox_container_config_init():
    """Test basic initialization of SandboxContainerConfig with various input combinations"""
    # Test with None values
    config = SandboxContainerConfig(None, None)
    assert config.container_base is None
    assert config.container_runtime is None

    # Test with string values
    config = SandboxContainerConfig("base-image", None)
    assert config.container_base == "base-image"
    assert config.container_runtime is None

def test_sandbox_container_config_str_conversion():
    """Test string type conversion in SandboxContainerConfig initialization"""
    # Test conversion from numeric values to strings
    config = SandboxContainerConfig(123, None)
    assert config.container_base == "123"
    assert config.container_runtime is None

    config = SandboxContainerConfig(None, 456)
    assert config.container_base is None
    assert config.container_runtime == "456"

def test_sandbox_container_config_both_images():
    """Test error handling when both container images are provided"""
    with pytest.raises(ValueError, match="Cannot provide both runtime and base container images."):
        SandboxContainerConfig("base-image", "runtime-image")

@mock.patch("openhands.__version__", "1.0.0")
def test_sandbox_container_config_build_default():
    """Test build_for_issue_resolver with default configuration"""
    config = SandboxContainerConfig.build_for_issue_resolver(None, None, False)
    assert config.container_base is None
    assert config.container_runtime == "ghcr.io/all-hands-ai/runtime:1.0.0-nikolaik"

def test_sandbox_container_config_build_experimental():
    """Test build_for_issue_resolver behavior in experimental mode"""
    config = SandboxContainerConfig.build_for_issue_resolver(None, None, True)
    assert config.container_base is None
    assert config.container_runtime is None

def test_sandbox_container_config_build_with_custom_images():
    """Test build_for_issue_resolver with custom container images"""
    # Test with base image
    config = SandboxContainerConfig.build_for_issue_resolver("custom-base", None, False)
    assert config.container_base == "custom-base"
    assert config.container_runtime is None

    # Test with runtime image
    config = SandboxContainerConfig.build_for_issue_resolver(None, "custom-runtime", False)
    assert config.container_base is None
    assert config.container_runtime == "custom-runtime"