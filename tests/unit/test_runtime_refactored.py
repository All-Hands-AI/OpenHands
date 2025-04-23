import os
import tempfile
from pathlib import Path
from unittest import mock

import pytest

from openhands.runtime.utils.runtime_build import (
    BuildFromImageType,
    _generate_dockerfile,
    build_deps_image,
    build_runtime_image,
    build_runtime_image_from_deps,
    get_deps_image_name,
)


class TestRuntimeRefactored:
    def test_get_deps_image_name(self):
        """Test that get_deps_image_name returns the expected name."""
        deps_image = get_deps_image_name()
        assert "oh_deps_v" in deps_image
        assert deps_image.startswith("ghcr.io/all-hands-ai/runtime:")

    def test_generate_dockerfile_deps(self):
        """Test that _generate_dockerfile generates the expected Dockerfile for DEPS build method."""
        dockerfile = _generate_dockerfile(
            base_image="ubuntu:22.04",
            build_from=BuildFromImageType.DEPS,
            deps_image="ghcr.io/all-hands-ai/runtime:oh_deps_v0.1.0",
        )
        assert "FROM ghcr.io/all-hands-ai/runtime:oh_deps_v0.1.0 as deps" in dockerfile
        assert "FROM ubuntu:22.04" in dockerfile
        assert "COPY --from=deps /openhands /openhands" in dockerfile

    @mock.patch("openhands.runtime.utils.runtime_build.RuntimeBuilder")
    def test_build_deps_image(self, mock_runtime_builder):
        """Test that build_deps_image calls the right methods."""
        mock_runtime_builder.build_image.return_value = "test_image"
        mock_runtime_builder.get_image.return_value = None

        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock the build process
            with mock.patch(
                "openhands.runtime.utils.runtime_build.build_deps_image_in_folder",
                return_value="test_deps_image",
            ):
                result = build_deps_image(
                    runtime_builder=mock_runtime_builder,
                    build_folder=temp_dir,
                    dry_run=True,
                )
                assert result == "test_deps_image"

    @mock.patch("openhands.runtime.utils.runtime_build.RuntimeBuilder")
    def test_build_runtime_image_from_deps(self, mock_runtime_builder):
        """Test that build_runtime_image_from_deps calls the right methods."""
        mock_runtime_builder.image_exists.return_value = False
        mock_runtime_builder.build_image.return_value = "test_image"

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create necessary directories
            os.makedirs(os.path.join(temp_dir, "code", "openhands"), exist_ok=True)

            # Mock the build process
            with mock.patch(
                "openhands.runtime.utils.runtime_build._build_sandbox_image",
                return_value="test_runtime_image",
            ):
                result = build_runtime_image_from_deps(
                    base_image="ubuntu:22.04",
                    runtime_builder=mock_runtime_builder,
                    deps_image="test_deps_image",
                    build_folder=Path(temp_dir),
                    dry_run=True,
                )
                assert "oh_deps_" in result

    @mock.patch("openhands.runtime.utils.runtime_build.RuntimeBuilder")
    def test_build_runtime_image_with_deps(self, mock_runtime_builder):
        """Test that build_runtime_image with use_deps_image=True calls the right methods."""
        mock_runtime_builder.get_image.return_value = "test_deps_image"

        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock the build process
            with mock.patch(
                "openhands.runtime.utils.runtime_build.build_runtime_image_from_deps",
                return_value="test_runtime_image",
            ):
                result = build_runtime_image(
                    base_image="ubuntu:22.04",
                    runtime_builder=mock_runtime_builder,
                    build_folder=temp_dir,
                    dry_run=True,
                    use_deps_image=True,
                    deps_image="test_deps_image",
                )
                assert result == "test_runtime_image"