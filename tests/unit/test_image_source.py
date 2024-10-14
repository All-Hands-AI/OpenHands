import os
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from docker.errors import ImageNotFound

from openhands import __version__
from openhands.runtime.image_source.build_image_source import BuildImageSource
from openhands.runtime.image_source.specific_image_source import SpecificImageSource


@pytest.mark.asyncio
async def test_specific_image_source_exists_locally():
    """
    Test the scenario where we have a specific docker image to use for the runtime
    ready to go locally.
    """
    docker_mock = MagicMock()
    image_mock = docker_mock.images.get()
    image_mock.tags = ['foobar:latest']
    source = SpecificImageSource('foobar', docker_client=docker_mock)
    image = await source.get_image()
    assert 'foobar:latest' == image
    docker_mock.images.get.assert_called_with('foobar')


@pytest.mark.asyncio
async def test_specific_image_source_not_exists_locally():
    """
    Test the scenario where we have a specific docker image to use for the runtime
    but it needs to be pulled from the remote source.
    """
    docker_mock = MagicMock()
    image_mock = MagicMock()
    image_mock.tags = ['foobar:latest']
    docker_mock.images.get.side_effect = [
        ImageNotFound("He doesn't like you either!"),
        image_mock,
    ]
    source = SpecificImageSource('foobar', docker_client=docker_mock)
    image = await source.get_image()
    assert 'foobar:latest' == image
    docker_mock.images.get.assert_called_with('foobar')
    assert docker_mock.images.get.call_count == 2
    docker_mock.api.pull.assert_called_with(
        'foobar', tag=None, stream=True, decode=True
    )


@pytest.mark.asyncio
async def test_build_image_name():
    """
    Test the process of building an image name. This is based on the current set of python files,
    so we mock this for consistency / test performance
    """

    async def mock_md5s_for_path(path, compiled_filter, md5s):
        md5s.update(
            {
                Path('foo'): b'\xac\xbf.\xe8\xb1\xad\xe4\xf1\xe0ov\xc6D\x01(\x94',
                Path('bar'): b'\xac\xbf.\xe8\xb1\xad\xe4\xf1\xe0ov\xc6D\x01(\x94',
            }
        )
        return md5s

    with patch(f'{BuildImageSource.__module__}.md5s_for_path', mock_md5s_for_path):
        source = BuildImageSource()
        name = await source.build_image_name()
        assert (
            name
            == f'ghcr.io/all-hands-ai/runtime:v{__version__}_d9910e731112cd3c037d6f6bfef65bee'
        )


@pytest.mark.asyncio
async def test_build_image_name_with_target():
    """
    Test the scenario where an image name is specified. No file hashing should be done
    """

    source = BuildImageSource(target_image='there/can-be:only_one')

    name = await source.build_image_name()
    assert name == 'there/can-be:only_one'


@pytest.mark.asyncio
async def test_build_project():
    """
    Test that build project command is executed with the correct parameters
    """
    subprocess_mock = MagicMock()
    subprocess_mock.PIPE = subprocess.PIPE
    subprocess_mock.run().returncode = 0

    with patch(f'{BuildImageSource.__module__}.subprocess', subprocess_mock):
        source = BuildImageSource()
        source.build_project(Path('mock-build'))

    subprocess_mock.run.assert_called_with(
        f"python -m build -s -o \"mock-build\" {os.getcwd().replace(' ', r'\ ')}",
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
