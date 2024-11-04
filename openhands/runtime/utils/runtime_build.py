import argparse
import hashlib
import os
import shutil
import string
import tempfile
from enum import Enum
from functools import wraps
from pathlib import Path
from typing import Any, Callable, List, TypeVar, Union

import docker
from dirhash import dirhash
from jinja2 import Environment, FileSystemLoader

import openhands
from openhands import __version__ as oh_version
from openhands.core.logger import openhands_logger as logger
from openhands.runtime.builder import DockerRuntimeBuilder, RuntimeBuilder


T = TypeVar('T')

def build_operation(operation_name: str) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator for build operations that handles common error patterns"""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            try:
                return func(*args, **kwargs)
            except (docker.errors.BuildError, docker.errors.APIError) as e:
                logger.error(f'Docker error during {operation_name}: {e}')
                raise RuntimeError(f'Docker build failed during {operation_name}: {str(e)}')
            except FileNotFoundError as e:
                logger.error(f'File not found during {operation_name}: {e}')
                raise RuntimeError(f'Missing file during {operation_name}: {str(e)}')
            except Exception as e:
                logger.error(f'Error during {operation_name}: {e}')
                raise RuntimeError(f'Build failed during {operation_name}: {str(e)}')
        return wrapper
    return decorator


class BuildFromImageType(Enum):
    SCRATCH = 'scratch'  # Slowest: Build from base image (no dependencies are reused)
    VERSIONED = 'versioned'  # Medium speed: Reuse the most recent image with the same base image & OH version
    LOCK = 'lock'  # Fastest: Reuse the most recent image with the exact SAME dependencies (lock files)


def get_runtime_image_repo() -> str:
    return os.getenv('OH_RUNTIME_RUNTIME_IMAGE_REPO', 'ghcr.io/all-hands-ai/runtime')


@build_operation("generate_dockerfile")
def _generate_dockerfile(
    base_image: str,
    build_from: BuildFromImageType = BuildFromImageType.SCRATCH,
    extra_deps: str | None = None,
) -> str:
    """Generate the Dockerfile content for the runtime image."""
    env = Environment(
        loader=FileSystemLoader(
            searchpath=os.path.join(os.path.dirname(__file__), 'runtime_templates')
        )
    )
    template = env.get_template('Dockerfile.j2')
    return template.render(
        base_image=base_image,
        build_from_scratch=build_from == BuildFromImageType.SCRATCH,
        build_from_versioned=build_from == BuildFromImageType.VERSIONED,
        extra_deps=extra_deps if extra_deps is not None else '',
    )


@build_operation("get_repo_tag")
def get_runtime_image_repo_and_tag(base_image: str) -> tuple[str, str]:
    """Get Docker repo and tag for the image."""
    if get_runtime_image_repo() in base_image:
        logger.debug(f'Using existing runtime image: [{base_image}]')
        if ':' not in base_image:
            base_image = base_image + ':latest'
        repo, tag = base_image.split(':')
        return repo, tag

    if ':' not in base_image:
        base_image = base_image + ':latest'
    [repo, tag] = base_image.split(':')

    if len(repo) > 32:
        repo_hash = hashlib.md5(repo[:-24].encode()).hexdigest()[:8]
        repo = f'{repo_hash}_{repo[-24:]}'
    else:
        repo = repo.replace('/', '_s_')

    new_tag = f'oh_v{oh_version}_image_{repo}_tag_{tag}'

    if len(new_tag) > 128:
        new_tag = f'oh_v{oh_version}_image_{hashlib.md5(new_tag.encode()).hexdigest()[:64]}'
        logger.warning(f'Tag too long, using hash: {new_tag}')

    return get_runtime_image_repo(), new_tag


@build_operation("build_image")
def build_runtime_image(
    base_image: str,
    runtime_builder: RuntimeBuilder,
    platform: str | None = None,
    extra_deps: str | None = None,
    build_folder: str | None = None,
    dry_run: bool = False,
    force_rebuild: bool = False,
) -> str:
    """Build the OpenHands runtime Docker image."""
    if build_folder is None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = build_runtime_image_in_folder(
                base_image=base_image,
                runtime_builder=runtime_builder,
                build_folder=Path(temp_dir),
                extra_deps=extra_deps,
                dry_run=dry_run,
                force_rebuild=force_rebuild,
                platform=platform,
            )
            return result

    result = build_runtime_image_in_folder(
        base_image=base_image,
        runtime_builder=runtime_builder,
        build_folder=Path(build_folder),
        extra_deps=extra_deps,
        dry_run=dry_run,
        force_rebuild=force_rebuild,
        platform=platform,
    )
    return result


@build_operation("build_in_folder")
def build_runtime_image_in_folder(
    base_image: str,
    runtime_builder: RuntimeBuilder,
    build_folder: Path,
    extra_deps: str | None,
    dry_run: bool,
    force_rebuild: bool,
    platform: str | None = None,
) -> str:
    """Build runtime image in specified folder."""
    runtime_image_repo, _ = get_runtime_image_repo_and_tag(base_image)
    lock_tag = f'oh_v{oh_version}_{get_hash_for_lock_files(base_image)}'
    versioned_tag = f'oh_v{oh_version}_{get_tag_for_versioned_image(base_image)}'
    versioned_image_name = f'{runtime_image_repo}:{versioned_tag}'
    source_tag = f'{lock_tag}_{get_hash_for_source_files()}'
    hash_image_name = f'{runtime_image_repo}:{source_tag}'

    logger.info(f'Building image: {hash_image_name}')
    if force_rebuild:
        logger.debug(f'Force rebuild from scratch: [{hash_image_name}]')
        prep_build_folder(
            build_folder,
            base_image,
            build_from=BuildFromImageType.SCRATCH,
            extra_deps=extra_deps,
        )
        if not dry_run:
            _build_sandbox_image(
                build_folder,
                runtime_builder,
                runtime_image_repo,
                source_tag,
                lock_tag,
                versioned_tag,
                platform,
            )
        return hash_image_name

    lock_image_name = f'{runtime_image_repo}:{lock_tag}'
    build_from = BuildFromImageType.SCRATCH

    if runtime_builder.image_exists(hash_image_name, False):
        logger.debug(f'Reusing existing image: [{hash_image_name}]')
        return hash_image_name

    if runtime_builder.image_exists(lock_image_name):
        logger.debug(f'Building from lock image: [{lock_image_name}]')
        build_from = BuildFromImageType.LOCK
        base_image = lock_image_name
    elif runtime_builder.image_exists(versioned_image_name):
        logger.info(f'Building from versioned image: [{versioned_image_name}]')
        build_from = BuildFromImageType.VERSIONED
        base_image = versioned_image_name
    else:
        logger.debug(f'Building from scratch: [{hash_image_name}]')

    prep_build_folder(build_folder, base_image, build_from, extra_deps)
    if not dry_run:
        _build_sandbox_image(
            build_folder,
            runtime_builder,
            runtime_image_repo,
            source_tag=source_tag,
            lock_tag=lock_tag,
            versioned_tag=versioned_tag if build_from == BuildFromImageType.SCRATCH else None,
            platform=platform,
        )

    return hash_image_name


@build_operation("prep_folder")
def prep_build_folder(
    build_folder: Path,
    base_image: str,
    build_from: BuildFromImageType,
    extra_deps: str | None,
) -> None:
    """Prepare build folder with source code and config files."""
    openhands_source_dir = Path(openhands.__file__).parent
    project_root = openhands_source_dir.parent
    logger.debug(f'Building from project root: {project_root}')

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

    for file in ['pyproject.toml', 'poetry.lock']:
        src = Path(openhands_source_dir, file)
        if not src.exists():
            src = Path(project_root, file)
        shutil.copy2(src, Path(build_folder, 'code', file))

    dockerfile_content = _generate_dockerfile(
        base_image,
        build_from=build_from,
        extra_deps=extra_deps,
    )
    with open(Path(build_folder, 'Dockerfile'), 'w') as file:
        file.write(dockerfile_content)


_ALPHABET = string.digits + string.ascii_lowercase


@build_operation("truncate_hash")
def truncate_hash(hash: str) -> str:
    """Convert base16 hash to base36 and truncate."""
    value = int(hash, 16)
    result: List[str] = []
    while value > 0 and len(result) < 16:
        value, remainder = divmod(value, len(_ALPHABET))
        result.append(_ALPHABET[remainder])
    return ''.join(result)


@build_operation("get_lock_hash")
def get_hash_for_lock_files(base_image: str) -> str:
    """Get hash for lock files."""
    openhands_source_dir = Path(openhands.__file__).parent
    md5 = hashlib.md5()
    md5.update(base_image.encode())
    for file in ['pyproject.toml', 'poetry.lock']:
        src = Path(openhands_source_dir, file)
        if not src.exists():
            src = Path(openhands_source_dir.parent, file)
        if not src.exists():
            raise FileNotFoundError(f'Cannot find {file} in {openhands_source_dir} or parent')
        with open(src, 'rb') as f:
            md5.update(f.read())
    return truncate_hash(md5.hexdigest())


@build_operation("get_source_hash")
def get_hash_for_source_files() -> str:
    """Get hash for source files."""
    openhands_source_dir = Path(openhands.__file__).parent
    hash = dirhash(
        openhands_source_dir,
        'md5',
        ignore=['*.pyc', '__pycache__', '*.md', '.*'],
    )
    return truncate_hash(hash)


@build_operation("get_versioned_tag")
def get_tag_for_versioned_image(base_image: str) -> str:
    """Get tag for versioned image."""
    md5 = hashlib.md5()
    md5.update(base_image.encode())
    return truncate_hash(md5.hexdigest())


@build_operation("build_sandbox")
def _build_sandbox_image(
    build_folder: Path,
    runtime_builder: RuntimeBuilder,
    runtime_image_repo: str,
    source_tag: str,
    lock_tag: str,
    versioned_tag: str | None,
    platform: str | None,
) -> None:
    """Build sandbox image with tags."""
    tags = [f'{runtime_image_repo}:{source_tag}']
    if versioned_tag:
        tags.append(f'{runtime_image_repo}:{versioned_tag}')
    tags.append(f'{runtime_image_repo}:{lock_tag}')

    runtime_builder.build(
        context=str(build_folder),
        tags=tags,
        platform=platform,
    )


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--base_image', type=str, default='nikolaik/python-nodejs:python3.12-nodejs22'
    )
    parser.add_argument('--build_folder', type=str, default=None)
    parser.add_argument('--force_rebuild', action='store_true', default=False)
    parser.add_argument('--platform', type=str, default=None)
    args = parser.parse_args()

    if args.build_folder is not None:
        # If a build_folder is provided, we do not actually build the Docker image. We copy the necessary source code
        # and create a Dockerfile dynamically and place it in the build_folder only. This allows the Docker image to
        # then be created using the Dockerfile (most likely using the containers/build.sh script)
        build_folder = args.build_folder
        assert os.path.exists(
            build_folder
        ), f'Build folder {build_folder} does not exist'
        logger.debug(
            f'Copying the source code and generating the Dockerfile in the build folder: {build_folder}'
        )

        runtime_image_repo, runtime_image_tag = get_runtime_image_repo_and_tag(
            args.base_image
        )
        logger.debug(
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
                platform=args.platform,
            )

            _runtime_image_repo, runtime_image_source_tag = (
                runtime_image_hash_name.split(':')
            )

            # Move contents of temp_dir to build_folder
            shutil.copytree(temp_dir, build_folder, dirs_exist_ok=True)
        logger.debug(
            f'Build folder [{build_folder}] is ready: {os.listdir(build_folder)}'
        )

        # We now update the config.sh in the build_folder to contain the required values. This is used in the
        # containers/build.sh script which is called to actually build the Docker image
        with open(os.path.join(build_folder, 'config.sh'), 'a') as file:
            file.write(
                (
                    f'\n'
                    f'DOCKER_IMAGE_TAG={runtime_image_tag}\n'
                    f'DOCKER_IMAGE_SOURCE_TAG={runtime_image_source_tag}\n'
                )
            )

        logger.debug(
            f'`config.sh` is updated with the image repo[{runtime_image_repo}] and tags [{runtime_image_tag}, {runtime_image_source_tag}]'
        )
        logger.debug(
            f'Dockerfile, source code and config.sh are ready in {build_folder}'
        )
    else:
        # If a build_folder is not provided, after copying the required source code and dynamically creating the
        # Dockerfile, we actually build the Docker image
        logger.debug('Building image in a temporary folder')
        docker_builder = DockerRuntimeBuilder(docker.from_env())
        image_name = build_runtime_image(
            args.base_image, docker_builder, platform=args.platform
        )
        logger.debug(f'\nBuilt image: {image_name}\n')

