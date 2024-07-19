import os
import tarfile
import tempfile
from importlib.metadata import version
from unittest.mock import MagicMock, patch

import pytest
import toml

from opendevin.runtime.utils.runtime_build import (
    _generate_dockerfile,
    _get_new_image_name,
    _put_source_code_to_dir,
    build_runtime_image,
)

RUNTIME_IMAGE_PREFIX = 'od_runtime'


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


def test_put_source_code_to_dir(temp_dir):
    folder_name = _put_source_code_to_dir(temp_dir)

    # assert there is a file called 'project.tar.gz' in the temp_dir
    assert os.path.exists(os.path.join(temp_dir, 'project.tar.gz'))

    # untar the file
    with tarfile.open(os.path.join(temp_dir, 'project.tar.gz'), 'r:gz') as tar:
        tar.extractall(path=temp_dir)

    # check the source file is the same as the current code base
    assert os.path.exists(os.path.join(temp_dir, folder_name, 'pyproject.toml'))
    # make sure the version from the pyproject.toml is the same as the current version
    with open(os.path.join(temp_dir, folder_name, 'pyproject.toml'), 'r') as f:
        pyproject = toml.load(f)
    _pyproject_version = pyproject['tool']['poetry']['version']
    assert _pyproject_version == version('opendevin')


def test_generate_dockerfile_scratch():
    base_image = 'debian:11'
    source_code_dirname = 'dummy'
    dockerfile_content = _generate_dockerfile(
        base_image,
        source_code_dirname=source_code_dirname,
        skip_init=False,
    )
    assert base_image in dockerfile_content
    assert 'RUN apt update && apt install -y wget sudo' in dockerfile_content
    assert (
        'RUN /opendevin/miniforge3/bin/mamba install conda-forge::poetry -y'
        in dockerfile_content
    )

    # Check the update command
    assert (
        f'RUN mv /opendevin/{source_code_dirname} /opendevin/code' in dockerfile_content
    )
    assert (
        '/opendevin/miniforge3/bin/mamba run -n base poetry install'
        in dockerfile_content
    )


def test_generate_dockerfile_skip_init():
    base_image = 'debian:11'
    source_code_dirname = 'dummy'
    dockerfile_content = _generate_dockerfile(
        base_image,
        source_code_dirname=source_code_dirname,
        skip_init=True,
    )

    # These commands SHOULD NOT include in the dockerfile if skip_init is True
    assert 'RUN apt update && apt install -y wget sudo' not in dockerfile_content
    assert (
        'RUN /opendevin/miniforge3/bin/mamba install conda-forge::poetry -y'
        not in dockerfile_content
    )

    # These update commands SHOULD still in the dockerfile
    assert (
        f'RUN mv /opendevin/{source_code_dirname} /opendevin/code' in dockerfile_content
    )
    assert (
        '/opendevin/miniforge3/bin/mamba run -n base poetry install'
        in dockerfile_content
    )


def test_get_new_image_name_eventstream():
    base_image = 'debian:11'
    new_image_name = _get_new_image_name(base_image)
    assert new_image_name == f'{RUNTIME_IMAGE_PREFIX}:debian_tag_11'

    base_image = 'ubuntu:22.04'
    new_image_name = _get_new_image_name(base_image)
    assert new_image_name == f'{RUNTIME_IMAGE_PREFIX}:ubuntu_tag_22.04'

    base_image = 'ubuntu'
    new_image_name = _get_new_image_name(base_image)
    assert new_image_name == f'{RUNTIME_IMAGE_PREFIX}:ubuntu_tag_latest'


def test_get_new_image_name_eventstream_dev_mode():
    base_image = f'{RUNTIME_IMAGE_PREFIX}:debian_tag_11'
    new_image_name = _get_new_image_name(base_image, dev_mode=True)
    assert new_image_name == f'{RUNTIME_IMAGE_PREFIX}_dev:debian_tag_11'

    base_image = f'{RUNTIME_IMAGE_PREFIX}:ubuntu_tag_22.04'
    new_image_name = _get_new_image_name(base_image, dev_mode=True)
    assert new_image_name == f'{RUNTIME_IMAGE_PREFIX}_dev:ubuntu_tag_22.04'

    base_image = f'{RUNTIME_IMAGE_PREFIX}:ubuntu_tag_latest'
    new_image_name = _get_new_image_name(base_image, dev_mode=True)
    assert new_image_name == f'{RUNTIME_IMAGE_PREFIX}_dev:ubuntu_tag_latest'


def test_get_new_image_name_eventstream_dev_invalid_base_image():
    with pytest.raises(ValueError):
        base_image = 'debian:11'
        _get_new_image_name(base_image, dev_mode=True)

    with pytest.raises(ValueError):
        base_image = 'ubuntu:22.04'
        _get_new_image_name(base_image, dev_mode=True)

    with pytest.raises(ValueError):
        base_image = 'ubuntu:latest'
        _get_new_image_name(base_image, dev_mode=True)


@patch('opendevin.runtime.utils.runtime_build._build_sandbox_image')
@patch('opendevin.runtime.utils.runtime_build.docker.DockerClient')
def test_build_runtime_image_from_scratch(mock_docker_client, mock_build_sandbox_image):
    base_image = 'debian:11'
    mock_docker_client.images.list.return_value = []

    image_name = build_runtime_image(base_image, mock_docker_client)
    assert image_name == f'{RUNTIME_IMAGE_PREFIX}:debian_tag_11'

    mock_build_sandbox_image.assert_called_once_with(
        base_image,
        f'{RUNTIME_IMAGE_PREFIX}:debian_tag_11',
        mock_docker_client,
        skip_init=False,
    )


@patch('opendevin.runtime.utils.runtime_build._build_sandbox_image')
@patch('opendevin.runtime.utils.runtime_build.docker.DockerClient')
def test_build_runtime_image_exist_no_update_source(
    mock_docker_client, mock_build_sandbox_image
):
    base_image = 'debian:11'
    mock_docker_client.images.list.return_value = [
        MagicMock(tags=[f'{RUNTIME_IMAGE_PREFIX}:debian_tag_11'])
    ]

    image_name = build_runtime_image(base_image, mock_docker_client)
    assert image_name == f'{RUNTIME_IMAGE_PREFIX}:debian_tag_11'

    mock_build_sandbox_image.assert_not_called()


@patch('opendevin.runtime.utils.runtime_build._build_sandbox_image')
@patch('opendevin.runtime.utils.runtime_build.docker.DockerClient')
def test_build_runtime_image_exist_with_update_source(
    mock_docker_client, mock_build_sandbox_image
):
    base_image = 'debian:11'
    mock_docker_client.images.list.return_value = [
        MagicMock(tags=[f'{RUNTIME_IMAGE_PREFIX}:debian_tag_11'])
    ]

    image_name = build_runtime_image(
        base_image, mock_docker_client, update_source_code=True
    )
    assert image_name == f'{RUNTIME_IMAGE_PREFIX}_dev:debian_tag_11'

    mock_build_sandbox_image.assert_called_once_with(
        f'{RUNTIME_IMAGE_PREFIX}:debian_tag_11',
        f'{RUNTIME_IMAGE_PREFIX}_dev:debian_tag_11',
        mock_docker_client,
        skip_init=True,
    )
