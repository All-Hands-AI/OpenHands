from unittest.mock import MagicMock, patch

from opendevin.runtime.docker.image_agnostic_util import (
    _get_new_image_name,
    generate_dockerfile_content,
    get_od_sandbox_image,
)


def test_generate_dockerfile_content():
    base_image = 'debian:11'
    dockerfile_content = generate_dockerfile_content(base_image)
    assert base_image in dockerfile_content
    assert (
        'RUN apt update && apt install -y openssh-server wget sudo'
        in dockerfile_content
    )


def test_get_new_image_name():
    base_image = 'debian:11'
    new_image_name = _get_new_image_name(base_image)
    assert new_image_name == 'od_sandbox:debian__11'

    base_image = 'ubuntu:22.04'
    new_image_name = _get_new_image_name(base_image)
    assert new_image_name == 'od_sandbox:ubuntu__22.04'

    base_image = 'ubuntu'
    new_image_name = _get_new_image_name(base_image)
    assert new_image_name == 'od_sandbox:ubuntu__latest'


@patch('opendevin.runtime.docker.image_agnostic_util._build_sandbox_image')
@patch('opendevin.runtime.docker.image_agnostic_util.docker.DockerClient')
def test_get_od_sandbox_image(mock_docker_client, mock_build_sandbox_image):
    base_image = 'debian:11'
    mock_docker_client.images.list.return_value = [
        MagicMock(tags=['od_sandbox:debian__11'])
    ]

    image_name = get_od_sandbox_image(base_image, mock_docker_client)
    assert image_name == 'od_sandbox:debian__11'

    mock_docker_client.images.list.return_value = []
    image_name = get_od_sandbox_image(base_image, mock_docker_client)
    assert image_name == 'od_sandbox:debian__11'
    mock_build_sandbox_image.assert_called_once_with(
        base_image, 'od_sandbox:debian__11', mock_docker_client
    )
