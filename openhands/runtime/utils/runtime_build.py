import argparse
import hashlib
import os
from pathlib import Path

from openhands import __version__
from openhands.core.logger import openhands_logger as logger
from openhands.runtime.image_source.build_image_source import BuildImageSource


def get_runtime_image_repo():
    return os.getenv('OH_RUNTIME_RUNTIME_IMAGE_REPO', 'ghcr.io/all-hands-ai/runtime')


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

        new_tag = f'oh_v{__version__}_image_{repo}_tag_{tag}'

        # if it's still too long, hash the entire image name
        if len(new_tag) > 128:
            new_tag = f'oh_v{__version__}_image_{hashlib.md5(new_tag.encode()).hexdigest()[:64]}'
            logger.warning(
                f'The new tag [{new_tag}] is still too long, so we use an hash of the entire image name: {new_tag}'
            )

        return get_runtime_image_repo(), new_tag


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

        # Suppose we just use image source here?
        # We use BuildImageSource here, but we just get the folder
        source = BuildImageSource(base_image=args.base_image, docker_client=None)
        docker_image_hash_tag = source.build_image_name()
        build_path = Path(build_folder)
        source.build_project(build_path)
        source.unzip_tarball(build_path)
        source.create_dockerfile(build_path)

        logger.info(
            f'Build folder [{build_folder}] is ready: {os.listdir(build_folder)}'
        )

        runtime_image_repo, runtime_image_tag = get_runtime_image_repo_and_tag(
            args.base_image
        )

        # We now update the config.sh in the build_folder to contain the required values. This is used in the
        # containers/build.sh script which is called to actually build the Docker image
        with open(os.path.join(build_folder, 'config.sh'), 'a') as file:
            file.write(
                (
                    f'\n'
                    f'DOCKER_IMAGE_TAG={runtime_image_tag}\n'
                    f'DOCKER_IMAGE_HASH_TAG={docker_image_hash_tag}\n'
                )
            )
        logger.info(
            f'`config.sh` is updated with the image repo[{runtime_image_repo}] and tags [{runtime_image_tag}, {docker_image_hash_tag}]'
        )
        logger.info(
            f'Dockerfile, source code and config.sh are ready in {build_folder}'
        )
    else:
        # If a build_folder is not provided, after copying the required source code and dynamically creating the
        # Dockerfile, we actually build the Docker image
        logger.info('Building image in a temporary folder')

        # Suppose we just use image source here?
        # We use BuildImageSource here

        source = BuildImageSource(
            base_image=args.base_image,
        )
        image_name = source.get_image()
        print(f'\nBUILT Image: {image_name}\n')
