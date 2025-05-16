import os
from unittest import mock

import pytest

from openhands.core.config import SandboxConfig
from openhands.resolver.resolve_issue import setup_sandbox_config, SandboxContainerConfig
import openhands

def assert_sandbox_config(
    config: SandboxConfig,
    base_container_image = SandboxConfig.model_fields["base_container_image"].default,
    runtime_container_image = "ghcr.io/all-hands-ai/runtime:mock-nikolaik",
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

class TestSandboxContainerConfig:
    """Test cases for SandboxContainerConfig"""

    def test_init_with_none_values(self):
        """Test initialization with None values"""
        config = SandboxContainerConfig(None, None)
        assert config.container_base is None
        assert config.container_runtime is None

    def test_init_with_string_values(self):
        """Test initialization with string values"""
        config = SandboxContainerConfig("base-image", None)
        assert config.container_base == "base-image"
        assert config.container_runtime is None

    def test_str_conversion(self):
        """Test automatic string conversion of input values"""
        config = SandboxContainerConfig(123, None)
        assert config.container_base == "123"
        assert config.container_runtime is None

        config = SandboxContainerConfig(None, 456)
        assert config.container_base is None
        assert config.container_runtime == "456"

    def test_both_images_raises_error(self):
        """Test that providing both images raises ValueError"""
        with pytest.raises(ValueError, match="Cannot provide both runtime and base container images."):
            SandboxContainerConfig("base-image", "runtime-image")

    @mock.patch("openhands.__version__", "mock")
    def test_build_default_config(self):
        """Test build_for_issue_resolver with default settings"""
        config = SandboxContainerConfig.build_for_issue_resolver(None, None, False)
        assert config.container_base is None
        assert config.container_runtime == "ghcr.io/all-hands-ai/runtime:mock-nikolaik"

    def test_build_experimental_config(self):
        """Test build_for_issue_resolver in experimental mode"""
        config = SandboxContainerConfig.build_for_issue_resolver(None, None, True)
        assert config.container_base is None
        assert config.container_runtime is None

    def test_build_with_custom_images(self):
        """Test build_for_issue_resolver with custom images"""
        base_config = SandboxContainerConfig.build_for_issue_resolver("custom-base", None, False)
        assert base_config.container_base == "custom-base"
        assert base_config.container_runtime is None

        runtime_config = SandboxContainerConfig.build_for_issue_resolver(None, "custom-runtime", False)
        assert runtime_config.container_base is None
        assert runtime_config.container_runtime == "custom-runtime"

class TestSetupSandboxConfig:
    """Test cases for setup_sandbox_config"""

    def test_default_configuration(self):
        """Test setup with default container configuration"""
        container_config = SandboxContainerConfig(None, "default-runtime")
        config = setup_sandbox_config(container_config)
        assert_sandbox_config(config, runtime_container_image="default-runtime")

    def test_base_image_configuration(self):
        """Test setup with base image configuration"""
        container_config = SandboxContainerConfig("custom-base", None)
        config = setup_sandbox_config(container_config)
        assert_sandbox_config(
            config,
            base_container_image="custom-base",
            runtime_container_image=None
        )

    def test_runtime_image_configuration(self):
        """Test setup with runtime image configuration"""
        container_config = SandboxContainerConfig(None, "custom-runtime")
        config = setup_sandbox_config(container_config)
        assert_sandbox_config(
            config,
            runtime_container_image="custom-runtime"
        )

    @mock.patch.dict("openhands.resolver.resolve_issue.os.environ", {"GITLAB_CI": "true"})
    @mock.patch("openhands.resolver.resolve_issue.os.getuid", return_value=0)
    @mock.patch("openhands.resolver.utils.get_unique_uid", return_value=1001)
    def test_gitlab_ci_root_configuration(self, mock_get_unique_uid, mock_getuid):
        """Test GitLab CI configuration when running as root"""
        container_config = SandboxContainerConfig(None, "runtime-image")
        config = setup_sandbox_config(container_config)
        assert_sandbox_config(
            config,
            runtime_container_image="runtime-image",
            local_runtime_url="http://localhost",
            user_id=1001
        )

    @mock.patch.dict("openhands.resolver.resolve_issue.os.environ", {"GITLAB_CI": "true"})
    @mock.patch("openhands.resolver.resolve_issue.os.getuid", return_value=1000)
    def test_gitlab_ci_non_root_configuration(self, mock_getuid):
        """Test GitLab CI configuration when not running as root"""
        container_config = SandboxContainerConfig(None, "runtime-image")
        config = setup_sandbox_config(container_config)
        assert_sandbox_config(
            config,
            runtime_container_image="runtime-image",
            local_runtime_url="http://localhost",
            user_id=1000
        )
