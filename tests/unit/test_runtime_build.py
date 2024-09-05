import os
import tempfile
from importlib.metadata import version
from unittest.mock import ANY, MagicMock, call, patch

import pytest
import toml
from pytest import TempPathFactory

from openhands.runtime.utils.runtime_build import (
    _generate_dockerfile,
    _get_package_version,
    _put_source_code_to_dir,
    build_runtime_image,
    get_runtime_image_repo,
    get_runtime_image_repo_and_tag,
    prep_docker_build_folder,
)

OH_VERSION = f'oh_v{_get_package_version()}'


@pytest.fixture
def temp_dir(tmp_path_factory: TempPathFactory) -> str:
    return str(tmp_path_factory.mktemp('test_runtime_build'))


def _check_source_code_in_dir(temp_dir):
    # assert there is a folder called 'code' in the temp_dir
    code_dir = os.path.join(temp_dir, 'code')
    assert os.path.exists(code_dir)
    assert os.path.isdir(code_dir)

    # check the source file is the same as the current code base
    assert os.path.exists(os.path.join(code_dir, 'pyproject.toml'))

    # The source code should only include the `openhands` folder, but not the other folders
    assert set(os.listdir(code_dir)) == {
        'agenthub',
        'openhands',
        'pyproject.toml',
        'poetry.lock',
        'LICENSE',
        'README.md',
        'PKG-INFO',
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
        base_image='nikolaik/python-nodejs:python3.11-nodejs22',
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
        base_image='nikolaik/python-nodejs:python3.11-nodejs22',
        skip_init=False,
    )

    with tempfile.TemporaryDirectory() as temp_dir_2:
        dir_hash_2 = prep_docker_build_folder(
            temp_dir_2,
            base_image='nikolaik/python-nodejs:python3.11-nodejs22',
            skip_init=False,
        )
    assert dir_hash_1 == dir_hash_2


# TODO where should the hash actually differ?
# def test_hash_folder_diff_init(temp_dir):
#     dir_hash_1 = prep_docker_build_folder(
#         temp_dir,
#         base_image='nikolaik/python-nodejs:python3.11-nodejs22',
#         skip_init=False,
#     )

#     with tempfile.TemporaryDirectory() as temp_dir_2:
#         dir_hash_2 = prep_docker_build_folder(
#             temp_dir_2,
#             base_image='nikolaik/python-nodejs:python3.11-nodejs22',
#             skip_init=True,
#         )
#     assert dir_hash_1 != dir_hash_2


# def test_hash_folder_diff_image(temp_dir):
#     dir_hash_1 = prep_docker_build_folder(
#         temp_dir,
#         base_image='nikolaik/python-nodejs:python3.11-nodejs22',
#         skip_init=False,
#     )

#     with tempfile.TemporaryDirectory() as temp_dir_2:
#         dir_hash_2 = prep_docker_build_folder(
#             temp_dir_2,
#             base_image='debian:11',
#             skip_init=False,
#         )
#     assert dir_hash_1 != dir_hash_2


def test_generate_dockerfile_scratch():
    base_image = 'debian:11'
    dockerfile_content = _generate_dockerfile(
        base_image,
        skip_init=False,
    )
    assert base_image in dockerfile_content
    assert 'apt-get update' in dockerfile_content
    assert 'apt-get install -y wget sudo apt-utils' in dockerfile_content
    assert (
        'RUN /openhands/miniforge3/bin/mamba install conda-forge::poetry python=3.11 -y'
        in dockerfile_content
    )

    # Check the update command
    assert 'COPY ./code /openhands/code' in dockerfile_content
    assert (
        '/openhands/miniforge3/bin/mamba run -n base poetry install'
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
    assert (
        'RUN /openhands/miniforge3/bin/mamba install conda-forge::poetry python=3.11 -y'
        not in dockerfile_content
    )

    # These update commands SHOULD still in the dockerfile
    assert 'COPY ./code /openhands/code' in dockerfile_content
    assert (
        '/openhands/miniforge3/bin/mamba run -n base poetry install'
        in dockerfile_content
    )


def test_get_runtime_image_repo_and_tag_eventstream():
    base_image = 'debian:11'
    img_repo, img_tag = get_runtime_image_repo_and_tag(base_image)
    assert (
        img_repo == f'{get_runtime_image_repo()}'
        and img_tag == f'{OH_VERSION}_image_debian_tag_11'
    )

    base_image = 'nikolaik/python-nodejs:python3.11-nodejs22'
    img_repo, img_tag = get_runtime_image_repo_and_tag(base_image)
    assert (
        img_repo == f'{get_runtime_image_repo()}'
        and img_tag
        == f'{OH_VERSION}_image_nikolaik_s_python-nodejs_tag_python3.11-nodejs22'
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

    mock_runtime_builder = MagicMock()
    mock_runtime_builder.image_exists.return_value = True

    # Mock the prep_docker_build_folder function to return a consistent hash
    with patch(
        'openhands.runtime.utils.runtime_build.prep_docker_build_folder'
    ) as mock_prep:
        mock_prep.return_value = 'mock_hash_123'

        image_name = build_runtime_image(base_image, mock_runtime_builder)

        # Assert that prep_docker_build_folder was called twice
        assert mock_prep.call_count == 1

        # Check the calls to prep_docker_build_folder
        mock_prep.assert_has_calls(
            [
                call(
                    ANY,
                    base_image=f'ghcr.io/all-hands-ai/runtime:{OD_VERSION}_image_debian_tag_11',
                    skip_init=True,
                    extra_deps=None,
                ),
            ]
        )

        # Assert that the image_exists method was called with the correct hash
        mock_runtime_builder.image_exists.assert_called_with(
            'ghcr.io/all-hands-ai/runtime:mock_hash_123'
        )

        # Assert that the build method was not called
        mock_runtime_builder.build.assert_not_called()

        # Check that the returned image name is correct
        assert image_name == 'ghcr.io/all-hands-ai/runtime:mock_hash_123'


@patch('openhands.runtime.utils.runtime_build._build_sandbox_image')
def test_build_runtime_image_exact_hash_not_exist(mock_build_sandbox_image, temp_dir):
    base_image = 'debian:11'
    repo, latest_image_tag = get_runtime_image_repo_and_tag(base_image)

    mock_runtime_builder = MagicMock()
    # Set up mock_runtime_builder.image_exists to return False for both checks
    mock_runtime_builder.image_exists.side_effect = [False, False]

    with patch(
        'openhands.runtime.utils.runtime_build.prep_docker_build_folder'
    ) as mock_prep_docker_build_folder:
        # We only expect prep_docker_build_folder to be called once now
        mock_prep_docker_build_folder.return_value = 'hash123'

        image_name = build_runtime_image(base_image, mock_runtime_builder)

        # Assert prep_docker_build_folder was called once with the correct arguments
        mock_prep_docker_build_folder.assert_called_once_with(
            ANY, base_image=base_image, skip_init=False, extra_deps=None
        )

        # Assert _build_sandbox_image was called with the correct arguments
        mock_build_sandbox_image.assert_called_once_with(
            docker_folder=ANY,
            runtime_builder=mock_runtime_builder,
            target_image_repo=repo,
            target_image_hash_tag='hash123',
            target_image_tag=latest_image_tag,
        )

        assert image_name == f'{repo}:hash123'

    # Verify that image_exists was called twice
    assert mock_runtime_builder.image_exists.call_count == 2
