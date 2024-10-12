import os
import tempfile
import uuid
from importlib.metadata import version
from unittest.mock import ANY, MagicMock, call, patch

import docker
import pytest
import toml
from pytest import TempPathFactory

from openhands import __version__ as oh_version
from openhands.core.logger import openhands_logger as logger
from openhands.runtime.builder.docker import DockerRuntimeBuilder
from openhands.runtime.utils.runtime_build import (
    _generate_dockerfile,
    _put_source_code_to_dir,
    build_runtime_image,
    get_runtime_image_repo,
    get_runtime_image_repo_and_tag,
    prep_docker_build_folder,
)

OH_VERSION = f'oh_v{oh_version}'
DEFAULT_BASE_IMAGE = 'nikolaik/python-nodejs:python3.12-nodejs22'


@pytest.fixture
def temp_dir(tmp_path_factory: TempPathFactory) -> str:
    return str(tmp_path_factory.mktemp('test_runtime_build'))


@pytest.fixture
def mock_docker_client():
    mock_client = MagicMock(spec=docker.DockerClient)
    mock_client.version.return_value = {
        'Version': '19.03'
    }  # Ensure version is >= 18.09
    return mock_client


@pytest.fixture
def docker_runtime_builder():
    client = docker.from_env()
    return DockerRuntimeBuilder(client)


def _check_source_code_in_dir(temp_dir):
    # assert there is a folder called 'code' in the temp_dir
    code_dir = os.path.join(temp_dir, 'code')
    assert os.path.exists(code_dir)
    assert os.path.isdir(code_dir)

    # check the source file is the same as the current code base
    assert os.path.exists(os.path.join(code_dir, 'pyproject.toml'))

    # The source code should only include the `openhands` folder,
    # and pyproject.toml & poetry.lock that are needed to build the runtime image
    assert set(os.listdir(code_dir)) == {
        'openhands',
        'pyproject.toml',
        'poetry.lock',
    }
    assert os.path.exists(os.path.join(code_dir, 'openhands'))
    assert os.path.isdir(os.path.join(code_dir, 'openhands'))

    # make sure the version from the pyproject.toml is the same as the current version
    with open(os.path.join(code_dir, 'pyproject.toml'), 'r') as f:
        pyproject = toml.load(f)

    _pyproject_version = pyproject['tool']['poetry']['version']
    assert _pyproject_version == version('openhands-ai')


def test_put_source_code_to_dir(temp_dir):
    _put_source_code_to_dir(temp_dir)
    _check_source_code_in_dir(temp_dir)


def test_docker_build_folder(temp_dir):
    prep_docker_build_folder(
        temp_dir,
        base_image=DEFAULT_BASE_IMAGE,
        skip_init=False,
    )

    # check the source code is in the folder
    _check_source_code_in_dir(temp_dir)

    # Now check dockerfile is in the folder
    dockerfile_path = os.path.join(temp_dir, 'Dockerfile')
    assert os.path.exists(dockerfile_path)
    assert os.path.isfile(dockerfile_path)

    # check the folder only contains the source code and the Dockerfile
    assert set(os.listdir(temp_dir)) == {'code', 'Dockerfile'}


def test_hash_folder_same(temp_dir):
    dir_hash_1 = prep_docker_build_folder(
        temp_dir,
        base_image=DEFAULT_BASE_IMAGE,
        skip_init=False,
    )

    with tempfile.TemporaryDirectory() as temp_dir_2:
        dir_hash_2 = prep_docker_build_folder(
            temp_dir_2,
            base_image=DEFAULT_BASE_IMAGE,
            skip_init=False,
        )
    assert dir_hash_1 == dir_hash_2


def test_hash_folder_diff_init(temp_dir):
    dir_hash_1 = prep_docker_build_folder(
        temp_dir,
        base_image=DEFAULT_BASE_IMAGE,
        skip_init=False,
    )

    with tempfile.TemporaryDirectory() as temp_dir_2:
        dir_hash_2 = prep_docker_build_folder(
            temp_dir_2,
            base_image=DEFAULT_BASE_IMAGE,
            skip_init=True,
        )
    assert dir_hash_1 != dir_hash_2


def test_hash_folder_diff_image(temp_dir):
    dir_hash_1 = prep_docker_build_folder(
        temp_dir,
        base_image=DEFAULT_BASE_IMAGE,
        skip_init=False,
    )

    with tempfile.TemporaryDirectory() as temp_dir_2:
        dir_hash_2 = prep_docker_build_folder(
            temp_dir_2,
            base_image='debian:11',
            skip_init=False,
        )
    assert dir_hash_1 != dir_hash_2


def test_generate_dockerfile_scratch():
    base_image = 'debian:11'
    dockerfile_content = _generate_dockerfile(
        base_image,
        skip_init=False,
    )
    assert base_image in dockerfile_content
    assert 'apt-get update' in dockerfile_content
    assert 'apt-get install -y wget curl sudo apt-utils' in dockerfile_content
    assert 'poetry' in dockerfile_content and '-c conda-forge' in dockerfile_content
    assert 'python=3.12' in dockerfile_content

    # Check the update command
    assert 'COPY ./code /openhands/code' in dockerfile_content
    assert (
        '/openhands/micromamba/bin/micromamba run -n openhands poetry install'
        in dockerfile_content
    )


def test_generate_dockerfile_skip_init():
    base_image = 'debian:11'
    dockerfile_content = _generate_dockerfile(
        base_image,
        skip_init=True,
    )

    # These commands SHOULD NOT include in the dockerfile if skip_init is True
    assert 'RUN apt update && apt install -y wget sudo' not in dockerfile_content
    assert '-c conda-forge' not in dockerfile_content
    assert 'python=3.12' not in dockerfile_content
    assert 'https://micro.mamba.pm/install.sh' not in dockerfile_content

    # These update commands SHOULD still in the dockerfile
    assert 'COPY ./code /openhands/code' in dockerfile_content
    assert 'poetry install' in dockerfile_content


def test_get_runtime_image_repo_and_tag_eventstream():
    base_image = 'debian:11'
    img_repo, img_tag = get_runtime_image_repo_and_tag(base_image)
    assert (
        img_repo == f'{get_runtime_image_repo()}'
        and img_tag == f'{OH_VERSION}_image_debian_tag_11'
    )

    img_repo, img_tag = get_runtime_image_repo_and_tag(DEFAULT_BASE_IMAGE)
    assert (
        img_repo == f'{get_runtime_image_repo()}'
        and img_tag
        == f'{OH_VERSION}_image_nikolaik_s_python-nodejs_tag_python3.12-nodejs22'
    )

    base_image = 'ubuntu'
    img_repo, img_tag = get_runtime_image_repo_and_tag(base_image)
    assert (
        img_repo == f'{get_runtime_image_repo()}'
        and img_tag == f'{OH_VERSION}_image_ubuntu_tag_latest'
    )


def test_build_runtime_image_from_scratch(temp_dir):
    base_image = 'debian:11'

    from_scratch_hash = prep_docker_build_folder(
        temp_dir,
        base_image,
        skip_init=False,
    )

    mock_runtime_builder = MagicMock()
    mock_runtime_builder.image_exists.return_value = False
    mock_runtime_builder.build.return_value = (
        f'{get_runtime_image_repo()}:{from_scratch_hash}'
    )

    image_name = build_runtime_image(base_image, mock_runtime_builder)
    mock_runtime_builder.build.assert_called_once_with(
        path=ANY,
        tags=[
            f'{get_runtime_image_repo()}:{from_scratch_hash}',
            f'{get_runtime_image_repo()}:{OH_VERSION}_image_debian_tag_11',
        ],
    )
    assert image_name == f'{get_runtime_image_repo()}:{from_scratch_hash}'


def test_build_runtime_image_exact_hash_exist(temp_dir):
    base_image = 'debian:11'

    from_scratch_hash = prep_docker_build_folder(
        temp_dir,
        base_image,
        skip_init=False,
    )

    mock_runtime_builder = MagicMock()
    mock_runtime_builder.image_exists.return_value = True
    mock_runtime_builder.build.return_value = (
        f'{get_runtime_image_repo()}:{from_scratch_hash}'
    )

    image_name = build_runtime_image(base_image, mock_runtime_builder)
    assert image_name == f'{get_runtime_image_repo()}:{from_scratch_hash}'
    mock_runtime_builder.build.assert_not_called()


@patch('openhands.runtime.utils.runtime_build._build_sandbox_image')
def test_build_runtime_image_exact_hash_not_exist(mock_build_sandbox_image, temp_dir):
    base_image = 'debian:11'
    repo, latest_image_tag = get_runtime_image_repo_and_tag(base_image)
    latest_image_name = f'{repo}:{latest_image_tag}'

    from_scratch_hash = prep_docker_build_folder(
        temp_dir,
        base_image,
        skip_init=False,
    )
    with tempfile.TemporaryDirectory() as temp_dir_2:
        non_from_scratch_hash = prep_docker_build_folder(
            temp_dir_2,
            base_image,
            skip_init=True,
        )

    mock_runtime_builder = MagicMock()
    # Set up mock_runtime_builder.image_exists to return False then True
    mock_runtime_builder.image_exists.side_effect = [False, True]

    with patch(
        'openhands.runtime.utils.runtime_build.prep_docker_build_folder'
    ) as mock_prep_docker_build_folder:
        mock_prep_docker_build_folder.side_effect = [
            from_scratch_hash,
            non_from_scratch_hash,
        ]

        image_name = build_runtime_image(base_image, mock_runtime_builder)

        mock_prep_docker_build_folder.assert_has_calls(
            [
                call(ANY, base_image=base_image, skip_init=False, extra_deps=None),
                call(
                    ANY, base_image=latest_image_name, skip_init=True, extra_deps=None
                ),
            ]
        )

        mock_build_sandbox_image.assert_called_once_with(
            docker_folder=ANY,
            runtime_builder=mock_runtime_builder,
            target_image_repo=repo,
            target_image_hash_tag=from_scratch_hash,
            target_image_tag=latest_image_tag,
        )
        assert image_name == f'{repo}:{from_scratch_hash}'


# ==============================
# DockerRuntimeBuilder Tests
# ==============================


def test_output_progress(docker_runtime_builder):
    with patch('sys.stdout.isatty', return_value=True):
        with patch('sys.stdout.write') as mock_write, patch('sys.stdout.flush'):
            docker_runtime_builder._output_logs('new log line')
            mock_write.assert_any_call('\033[F' * 10)
            mock_write.assert_any_call('\033[2Knew log line\n')


def test_output_build_progress(docker_runtime_builder):
    with patch('sys.stdout.isatty', return_value=True):
        with patch('sys.stdout.write') as mock_write, patch('sys.stdout.flush'):
            layers = {}
            docker_runtime_builder._output_build_progress(
                {
                    'id': 'layer1',
                    'status': 'Downloading',
                    'progressDetail': {'current': 50, 'total': 100},
                },
                layers,
                0,
            )
            mock_write.assert_any_call('\033[F' * 0)
            mock_write.assert_any_call('\033[2K\r')
            assert layers['layer1']['status'] == 'Downloading'
            assert layers['layer1']['progress'] == ''
            assert layers['layer1']['last_logged'] == 50.0


@pytest.fixture(scope='function')
def live_docker_image():
    client = docker.from_env()
    unique_id = str(uuid.uuid4())[:8]  # Use first 8 characters of a UUID
    unique_prefix = f'test_image_{unique_id}'

    dockerfile_content = f"""
    # syntax=docker/dockerfile:1.4
    FROM {DEFAULT_BASE_IMAGE} AS base
    RUN apt-get update && apt-get install -y wget curl sudo apt-utils

    FROM base AS intermediate
    RUN mkdir -p /openhands

    FROM intermediate AS final
    RUN echo "Hello, OpenHands!" > /openhands/hello.txt
    """

    with tempfile.TemporaryDirectory() as temp_dir:
        dockerfile_path = os.path.join(temp_dir, 'Dockerfile')
        with open(dockerfile_path, 'w') as f:
            f.write(dockerfile_content)

        try:
            image, logs = client.images.build(
                path=temp_dir,
                tag=f'{unique_prefix}:final',
                buildargs={'DOCKER_BUILDKIT': '1'},
                labels={'test': 'true'},
                rm=True,
                forcerm=True,
            )

            # Tag intermediary stages
            client.api.tag(image.id, unique_prefix, 'base')
            client.api.tag(image.id, unique_prefix, 'intermediate')

            all_tags = [
                f'{unique_prefix}:final',
                f'{unique_prefix}:base',
                f'{unique_prefix}:intermediate',
            ]

            print(f'\nImage ID: {image.id}')
            print(f'Image tags: {all_tags}\n')

            yield image

        finally:
            # Clean up all tagged images
            for tag in all_tags:
                try:
                    client.images.remove(tag, force=True)
                    print(f'Removed image: {tag}')
                except Exception as e:
                    print(f'Error removing image {tag}: {str(e)}')


def test_init(docker_runtime_builder):
    assert isinstance(docker_runtime_builder.docker_client, docker.DockerClient)
    assert docker_runtime_builder.max_lines == 10
    assert docker_runtime_builder.log_lines == [''] * 10


def test_build_image_from_scratch(docker_runtime_builder, tmp_path):
    context_path = str(tmp_path)
    tags = ['test_build:latest']

    # Create a minimal Dockerfile in the context path
    with open(os.path.join(context_path, 'Dockerfile'), 'w') as f:
        f.write("""FROM php:latest
CMD ["sh", "-c", "echo 'Hello, World!'"]
""")
    built_image_name = None
    container = None
    client = docker.from_env()
    try:
        with patch('sys.stdout.isatty', return_value=False):
            built_image_name = docker_runtime_builder.build(
                context_path,
                tags,
                use_local_cache=False,
            )
            assert built_image_name == f'{tags[0]}'

            # Verify the image was created
            image = client.images.get(tags[0])
            assert image is not None

    except docker.errors.ImageNotFound:
        pytest.fail('test_build_image_from_scratch: test image not found!')
    except Exception as e:
        pytest.fail(f'test_build_image_from_scratch: Build failed with error: {str(e)}')

    finally:
        # Clean up the container
        if container:
            try:
                container.remove(force=True)
                logger.info(f'Removed test container: `{container.id}`')
            except Exception as e:
                logger.warning(
                    f'Failed to remove test container `{container.id}`: {str(e)}'
                )

        # Clean up the image
        if built_image_name:
            try:
                client.images.remove(built_image_name, force=True)
                logger.info(f'Removed test image: `{built_image_name}`')
            except Exception as e:
                logger.warning(
                    f'Failed to remove test image `{built_image_name}`: {str(e)}'
                )
        else:
            logger.warning('No image was built, so no image cleanup was necessary.')


def _format_size_to_gb(bytes_size):
    """Convert bytes to gigabytes with two decimal places."""
    return round(bytes_size / (1024**3), 2)


def test_list_dangling_images():
    client = docker.from_env()
    dangling_images = client.images.list(filters={'dangling': True})
    if dangling_images and len(dangling_images) > 0:
        for image in dangling_images:
            if 'Size' in image.attrs and isinstance(image.attrs['Size'], int):
                size_gb = _format_size_to_gb(image.attrs['Size'])
                logger.info(f'Dangling image: {image.tags}, Size: {size_gb} GB')
            else:
                logger.info(f'Dangling image: {image.tags}, Size: n/a')
    else:
        logger.info('No dangling images found')


def test_build_image_from_repo(docker_runtime_builder, tmp_path):
    context_path = str(tmp_path)
    tags = ['alpine:latest']

    # Create a minimal Dockerfile in the context path
    with open(os.path.join(context_path, 'Dockerfile'), 'w') as f:
        f.write(f"""FROM {DEFAULT_BASE_IMAGE}
CMD ["sh", "-c", "echo 'Hello, World!'"]
""")
    built_image_name = None
    container = None
    client = docker.from_env()
    try:
        with patch('sys.stdout.isatty', return_value=False):
            built_image_name = docker_runtime_builder.build(
                context_path,
                tags,
                use_local_cache=False,
            )
            assert built_image_name == f'{tags[0]}'

            image = client.images.get(tags[0])
            assert image is not None

    except docker.errors.ImageNotFound:
        pytest.fail('test_build_image_from_repo: test image not found!')

    finally:
        # Clean up the container
        if container:
            try:
                container.remove(force=True)
                logger.info(f'Removed test container: `{container.id}`')
            except Exception as e:
                logger.warning(
                    f'Failed to remove test container `{container.id}`: {str(e)}'
                )

        # Clean up the image
        if built_image_name:
            try:
                client.images.remove(built_image_name, force=True)
                logger.info(f'Removed test image: `{built_image_name}`')
            except Exception as e:
                logger.warning(
                    f'Failed to remove test image `{built_image_name}`: {str(e)}'
                )
        else:
            logger.warning('No image was built, so no image cleanup was necessary.')


def test_image_exists_local(docker_runtime_builder, live_docker_image):
    image_name = live_docker_image.tags[0] if live_docker_image.tags else None
    assert image_name, 'Image has no tags'
    assert docker_runtime_builder.image_exists(image_name)


def test_image_exists_not_found(docker_runtime_builder):
    assert not docker_runtime_builder.image_exists('nonexistent:image')
