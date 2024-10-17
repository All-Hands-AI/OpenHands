import argparse
import hashlib
import os
import shutil
import string
import tempfile
from pathlib import Path
from typing import List

import docker
from dirhash import dirhash
from jinja2 import Environment, FileSystemLoader

import openhands
from openhands import __version__ as oh_version
from openhands.core.logger import openhands_logger as logger
from openhands.runtime.builder import DockerRuntimeBuilder, RuntimeBuilder


def get_runtime_image_repo():
    return os.getenv('OH_RUNTIME_RUNTIME_IMAGE_REPO', 'ghcr.io/all-hands-ai/runtime')


def _generate_dockerfile(
    base_image: str,
    build_from_scratch: bool = True,
    extra_deps: str | None = None,
) -> str:
    """Generate the Dockerfile content for the runtime image based on the base image.

    Parameters:
    - base_image (str): The base image provided for the runtime image
    - build_from_scratch (boolean): False implies most steps can be skipped (Base image is another openhands instance)
    - extra_deps (str):

    Returns:
    - str: The resulting Dockerfile content
    """
    env = Environment(
        loader=FileSystemLoader(
            searchpath=os.path.join(os.path.dirname(__file__), 'runtime_templates')
        )
    )
    template = env.get_template('Dockerfile.j2')

    dockerfile_content = template.render(
        base_image=base_image,
        build_from_scratch=build_from_scratch,
        extra_deps=extra_deps if extra_deps is not None else '',
    )
    return dockerfile_content


def get_runtime_image_repo_and_tag(base_image: str) -> tuple[str, str]:
    """Retrieves the Docker repo and tag associated with the Docker image.

    Parameters:
    - base_image (str): The name of the base Docker image

    Returns:
    - tuple[str, str]: The Docker repo and tag of the Docker image
    """

    if get_runtime_image_repo() in base_image:
        logger.info(
            f'The provided image [{base_image}] is already a valid runtime image.\n'
            f'Will try to reuse it as is.'
        )

        if ':' not in base_image:
            base_image = base_image + ':latest'
        repo, tag = base_image.split(':')
        return repo, tag
    else:
        if ':' not in base_image:
            base_image = base_image + ':latest'
        [repo, tag] = base_image.split(':')

        # Hash the repo if it's too long
        if len(repo) > 32:
            repo_hash = hashlib.md5(repo[:-24].encode()).hexdigest()[:8]
            repo = f'{repo_hash}_{repo[-24:]}'  # Use 8 char hash + last 24 chars
        else:
            repo = repo.replace('/', '_s_')

        new_tag = f'oh_v{oh_version}_image_{repo}_tag_{tag}'

        # if it's still too long, hash the entire image name
        if len(new_tag) > 128:
            new_tag = f'oh_v{oh_version}_image_{hashlib.md5(new_tag.encode()).hexdigest()[:64]}'
            logger.warning(
                f'The new tag [{new_tag}] is still too long, so we use an hash of the entire image name: {new_tag}'
            )

        return get_runtime_image_repo(), new_tag


def build_runtime_image(
    base_image: str,
    runtime_builder: RuntimeBuilder,
    extra_deps: str | None = None,
    build_folder: str | None = None,
    dry_run: bool = False,
    force_rebuild: bool = False,
) -> str:
    """Prepares the final docker build folder.
    If dry_run is False, it will also build the OpenHands runtime Docker image using the docker build folder.

    Parameters:
    - base_image (str): The name of the base Docker image to use
    - runtime_builder (RuntimeBuilder): The runtime builder to use
    - extra_deps (str):
    - build_folder (str): The directory to use for the build. If not provided a temporary directory will be used
    - dry_run (bool): if True, it will only ready the build folder. It will not actually build the Docker image
    - force_rebuild (bool): if True, it will create the Dockerfile which uses the base_image

    Returns:
    - str: <image_repo>:<MD5 hash>. Where MD5 hash is the hash of the docker build folder

    See https://docs.all-hands.dev/modules/usage/architecture/runtime for more details.
    """
    if build_folder is None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = build_runtime_image_in_folder(
                base_image=base_image,
                runtime_builder=runtime_builder,
                build_folder=Path(temp_dir),
                extra_deps=extra_deps,
                dry_run=dry_run,
                force_rebuild=force_rebuild,
            )
            return result

    result = build_runtime_image_in_folder(
        base_image=base_image,
        runtime_builder=runtime_builder,
        build_folder=Path(build_folder),
        extra_deps=extra_deps,
        dry_run=dry_run,
        force_rebuild=force_rebuild,
    )
    return result


def build_runtime_image_in_folder(
    base_image: str,
    runtime_builder: RuntimeBuilder,
    build_folder: Path,
    extra_deps: str | None,
    dry_run: bool,
    force_rebuild: bool,
) -> str:
    runtime_image_repo, _ = get_runtime_image_repo_and_tag(base_image)
    lock_tag = f'oh_v{oh_version}_{get_hash_for_lock_files(base_image)}'
    hash_tag = f'{lock_tag}_{get_hash_for_source_files()}'
    hash_image_name = f'{runtime_image_repo}:{hash_tag}'

    if force_rebuild:
        logger.info(f'Force rebuild: [{runtime_image_repo}:{hash_tag}] from scratch.')
        prep_build_folder(build_folder, base_image, True, extra_deps)
        if not dry_run:
            _build_sandbox_image(
                build_folder,
                runtime_builder,
                runtime_image_repo,
                hash_tag,
                lock_tag,
            )
        return hash_image_name

    lock_image_name = f'{runtime_image_repo}:{lock_tag}'
    build_from_scratch = True

    # If the exact image already exists, we do not need to build it
    if runtime_builder.image_exists(hash_image_name, False):
        logger.info(f'Reusing Image [{hash_image_name}]')
        return hash_image_name

    # We look for an existing image that shares the same lock_tag. If such an image exists, we
    # can use it as the base image for the build and just copy source files. This makes the build
    # much faster.
    if runtime_builder.image_exists(lock_image_name):
        logger.info(f'Build [{hash_image_name}] from [{lock_image_name}]')
        build_from_scratch = False
        base_image = lock_image_name
    else:
        logger.info(f'Build [{hash_image_name}] from scratch')

    prep_build_folder(build_folder, base_image, build_from_scratch, extra_deps)
    if not dry_run:
        _build_sandbox_image(
            build_folder,
            runtime_builder,
            runtime_image_repo,
            hash_tag,
            lock_tag,
        )

    return hash_image_name


def prep_build_folder(
    build_folder: Path,
    base_image: str,
    build_from_scratch: bool,
    extra_deps: str | None,
):
    # Copy the source code to directory. It will end up in build_folder/code
    # If package is not found, build from source code
    openhands_source_dir = Path(openhands.__file__).parent
    project_root = openhands_source_dir.parent
    logger.info(f'Building source distribution using project root: {project_root}')

    # Copy the 'openhands' directory (Source code)
    shutil.copytree(
        openhands_source_dir,
        Path(build_folder, 'code', 'openhands'),
        ignore=shutil.ignore_patterns(
            '.*/',
            '__pycache__/',
            '*.pyc',
            '*.md',
        ),
    )

    # Copy pyproject.toml and poetry.lock files
    for file in ['pyproject.toml', 'poetry.lock']:
        src = Path(openhands_source_dir, file)
        if not src.exists():
            src = Path(project_root, file)
        shutil.copy2(src, Path(build_folder, 'code', file))

    # Create a Dockerfile and write it to build_folder
    dockerfile_content = _generate_dockerfile(
        base_image,
        build_from_scratch=build_from_scratch,
        extra_deps=extra_deps,
    )
    with open(Path(build_folder, 'Dockerfile'), 'w') as file:  # type: ignore
        file.write(dockerfile_content)  # type: ignore


_ALPHABET = string.digits + string.ascii_lowercase


def truncate_hash(hash: str) -> str:
    """Convert the base16 hash to base36 and truncate at 16 characters."""
    value = int(hash, 16)
    result: List[str] = []
    while value > 0 and len(result) < 16:
        value, remainder = divmod(value, len(_ALPHABET))
        result.append(_ALPHABET[remainder])
    return ''.join(result)


def get_hash_for_lock_files(base_image: str):
    openhands_source_dir = Path(openhands.__file__).parent
    md5 = hashlib.md5()
    md5.update(base_image.encode())
    for file in ['pyproject.toml', 'poetry.lock']:
        src = Path(openhands_source_dir, file)
        if not src.exists():
            src = Path(openhands_source_dir.parent, file)
        with open(src, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                md5.update(chunk)
    # We get away with truncation because we want something that is unique
    # rather than something that is cryptographically secure
    result = truncate_hash(md5.hexdigest())
    return result


def get_hash_for_source_files():
    openhands_source_dir = Path(openhands.__file__).parent
    dir_hash = dirhash(
        openhands_source_dir,
        'md5',
        ignore=[
            '.*/',  # hidden directories
            '__pycache__/',
            '*.pyc',
        ],
    )
    # We get away with truncation because we want something that is unique
    # rather than something that is cryptographically secure
    result = truncate_hash(dir_hash)
    return result


def _build_sandbox_image(
    build_folder: Path,
    runtime_builder: RuntimeBuilder,
    runtime_image_repo: str,
    hash_tag: str,
    lock_tag: str,
):
    """Build and tag the sandbox image. The image will be tagged with all tags that do not yet exist"""

    names = [
        name
        for name in [
            f'{runtime_image_repo}:{hash_tag}',
            f'{runtime_image_repo}:{lock_tag}',
        ]
        if not runtime_builder.image_exists(name, False)
    ]

    image_name = runtime_builder.build(path=str(build_folder), tags=names)
    if not image_name:
        raise RuntimeError(f'Build failed for image {names}')

    return image_name


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--base_image', type=str, default='nikolaik/python-nodejs:python3.12-nodejs22'
    )
    parser.add_argument('--build_folder', type=str, default=None)
    parser.add_argument('--force_rebuild', action='store_true', default=False)
    args = parser.parse_args()

    if args.build_folder is not None:
        # If a build_folder is provided, we do not actually build the Docker image. We copy the necessary source code
        # and create a Dockerfile dynamically and place it in the build_folder only. This allows the Docker image to
        # then be created using the Dockerfile (most likely using the containers/build.sh script)
        build_folder = args.build_folder
        assert os.path.exists(
            build_folder
        ), f'Build folder {build_folder} does not exist'
        logger.info(
            f'Copying the source code and generating the Dockerfile in the build folder: {build_folder}'
        )

        runtime_image_repo, runtime_image_tag = get_runtime_image_repo_and_tag(
            args.base_image
        )
        logger.info(
            f'Runtime image repo: {runtime_image_repo} and runtime image tag: {runtime_image_tag}'
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            # dry_run is true so we only prepare a temp_dir containing the required source code and the Dockerfile. We
            # then obtain the MD5 hash of the folder and return <image_repo>:<temp_dir_md5_hash>
            runtime_image_hash_name = build_runtime_image(
                args.base_image,
                runtime_builder=DockerRuntimeBuilder(docker.from_env()),
                build_folder=temp_dir,
                dry_run=True,
                force_rebuild=args.force_rebuild,
            )

            _runtime_image_repo, runtime_image_hash_tag = runtime_image_hash_name.split(
                ':'
            )

            # Move contents of temp_dir to build_folder
            shutil.copytree(temp_dir, build_folder, dirs_exist_ok=True)
        logger.info(
            f'Build folder [{build_folder}] is ready: {os.listdir(build_folder)}'
        )

        # We now update the config.sh in the build_folder to contain the required values. This is used in the
        # containers/build.sh script which is called to actually build the Docker image
        with open(os.path.join(build_folder, 'config.sh'), 'a') as file:
            file.write(
                (
                    f'\n'
                    f'DOCKER_IMAGE_TAG={runtime_image_tag}\n'
                    f'DOCKER_IMAGE_HASH_TAG={runtime_image_hash_tag}\n'
                )
            )
        logger.info(
            f'`config.sh` is updated with the image repo[{runtime_image_repo}] and tags [{runtime_image_tag}, {runtime_image_hash_tag}]'
        )
        logger.info(
            f'Dockerfile, source code and config.sh are ready in {build_folder}'
        )
    else:
        # If a build_folder is not provided, after copying the required source code and dynamically creating the
        # Dockerfile, we actually build the Docker image
        logger.info('Building image in a temporary folder')
        docker_builder = DockerRuntimeBuilder(docker.from_env())
        image_name = build_runtime_image(args.base_image, docker_builder)
        print(f'\nBUILT Image: {image_name}\n')
