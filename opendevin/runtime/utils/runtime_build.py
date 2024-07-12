import argparse
import os
import shutil
import tempfile

import docker

from opendevin.core.logger import opendevin_logger as logger

from .source import create_project_source_dist


def _generate_dockerfile(
    base_image: str, temp_dir: str, skip_init: bool = False
) -> str:
    """
    Generate the Dockerfile content for the eventstream runtime image based on user-provided base image.

    NOTE: This is only tested on debian yet.
    """
    if skip_init:
        dockerfile_content = f'FROM {base_image}\n'
    else:
        dockerfile_content = (
            f'FROM {base_image}\n'
            # FIXME: make this more generic / cross-platform
            'RUN apt update && apt install -y wget sudo\n'
            'RUN apt-get update && apt-get install -y libgl1-mesa-glx\n'  # Extra dependency for OpenCV
            'RUN mkdir -p /opendevin && mkdir -p /opendevin/logs && chmod 777 /opendevin/logs\n'
            'RUN echo "" > /opendevin/bash.bashrc\n'
            'RUN if [ ! -d /opendevin/miniforge3 ]; then \\\n'
            '        wget --progress=bar:force -O Miniforge3.sh "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh" && \\\n'
            '        bash Miniforge3.sh -b -p /opendevin/miniforge3 && \\\n'
            '        rm Miniforge3.sh && \\\n'
            '        chmod -R g+w /opendevin/miniforge3 && \\\n'
            '        bash -c ". /opendevin/miniforge3/etc/profile.d/conda.sh && conda config --set changeps1 False && conda config --append channels conda-forge"; \\\n'
            '    fi\n'
            'RUN /opendevin/miniforge3/bin/mamba install python=3.11 -y\n'
            'RUN /opendevin/miniforge3/bin/mamba install conda-forge::poetry -y\n'
        )

    tarball_path = create_project_source_dist()
    filename = os.path.basename(tarball_path)
    filename = filename.removesuffix('.tar.gz')

    # move the tarball to temp_dir
    _res = shutil.copy(tarball_path, os.path.join(temp_dir, 'project.tar.gz'))
    if _res:
        os.remove(tarball_path)
    logger.info(
        f'Source distribution moved to {os.path.join(temp_dir, "project.tar.gz")}'
    )

    # Copy the project directory to the container
    dockerfile_content += 'COPY project.tar.gz /opendevin\n'
    # remove /opendevin/code if it exists
    dockerfile_content += (
        'RUN if [ -d /opendevin/code ]; then rm -rf /opendevin/code; fi\n'
    )
    # unzip the tarball to /opendevin/code
    dockerfile_content += (
        'RUN cd /opendevin && tar -xzvf project.tar.gz && rm project.tar.gz\n'
    )
    dockerfile_content += f'RUN mv /opendevin/{filename} /opendevin/code\n'
    # install (or update) the dependencies
    dockerfile_content += (
        'RUN cd /opendevin/code && '
        '/opendevin/miniforge3/bin/mamba run -n base poetry env use python3.11 && '
        '/opendevin/miniforge3/bin/mamba run -n base poetry install\n'
        # for browser (update if needed)
        'RUN apt-get update && cd /opendevin/code && /opendevin/miniforge3/bin/mamba run -n base poetry run playwright install --with-deps chromium\n'
    )
    return dockerfile_content


def _build_sandbox_image(
    base_image: str,
    target_image_name: str,
    docker_client: docker.DockerClient,
    skip_init: bool = False,
):
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            dockerfile_content = _generate_dockerfile(
                base_image, temp_dir, skip_init=skip_init
            )
            if skip_init:
                logger.info(
                    f'Reusing existing od_sandbox image [{target_image_name}] but will update the source code in it.'
                )
                logger.info(
                    (
                        f'===== Dockerfile content =====\n'
                        f'{dockerfile_content}\n'
                        f'==============================='
                    )
                )
            else:
                logger.info(f'Building agnostic sandbox image: {target_image_name}')
                logger.info(
                    (
                        f'===== Dockerfile content =====\n'
                        f'{dockerfile_content}\n'
                        f'==============================='
                    )
                )
            with open(f'{temp_dir}/Dockerfile', 'w') as file:
                file.write(dockerfile_content)

            api_client = docker_client.api
            build_logs = api_client.build(
                path=temp_dir,
                tag=target_image_name,
                rm=True,
                decode=True,
                # do not use cache when skip_init is True (i.e., when we want to update the source code in the existing image)
                nocache=skip_init,
            )

            if skip_init:
                logger.info(
                    f'Rebuilding existing od_sandbox image [{target_image_name}] to update the source code.'
                )
            for log in build_logs:
                if 'stream' in log:
                    print(log['stream'].strip())
                elif 'error' in log:
                    logger.error(log['error'].strip())
                else:
                    logger.info(str(log))

        logger.info(f'Image {target_image_name} built successfully')
    except docker.errors.BuildError as e:
        logger.error(f'Sandbox image build failed: {e}')
        raise e
    except Exception as e:
        logger.error(f'An error occurred during sandbox image build: {e}')
        raise e


def _get_new_image_name(base_image: str, dev_mode: bool = False) -> str:
    if dev_mode:
        prefix = 'od_runtime_dev'
    else:
        prefix = 'od_runtime'

    if ':' not in base_image:
        base_image = base_image + ':latest'
    [repo, tag] = base_image.split(':')
    repo = repo.replace('/', '___')
    return f'{prefix}:{repo}_tag_{tag}'


def _check_image_exists(base_image: str, docker_client: docker.DockerClient) -> bool:
    new_image_name = _get_new_image_name(base_image)
    images = docker_client.images.list()
    for image in images:
        if new_image_name in image.tags:
            return True
    return False


def build_runtime_image(
    base_image: str,
    docker_client: docker.DockerClient,
    update_source_code: bool = False,
) -> str:
    """Build the runtime image for the OpenDevin runtime.

    This is only used for **eventstream runtime**.
    """
    new_image_name = _get_new_image_name(base_image)

    # Try to pull the new image from the registry
    try:
        docker_client.images.pull(new_image_name)
    except docker.errors.ImageNotFound:
        logger.info(f'Image {new_image_name} not found, building it from scratch')

    # Detect if the sandbox image is built
    image_exists = _check_image_exists(base_image, docker_client)

    skip_init = False
    if image_exists and not update_source_code:
        # If (1) Image exists & we are not updating the source code, we can reuse the existing production image
        return new_image_name
    elif image_exists and update_source_code:
        # If (2) Image exists & we plan to update the source code (in dev mode), we need to rebuild the image
        # and give it a special name
        # e.g., od_runtime:ubuntu_tag_latest -> od_runtime_dev:ubuntu_tag_latest
        base_image = new_image_name
        new_image_name = _get_new_image_name(base_image, dev_mode=True)

        skip_init = True  # since we only need to update the source code
    else:
        # If (3) Image does not exist, we need to build it from scratch
        # e.g., ubuntu:latest -> od_runtime:ubuntu_tag_latest
        skip_init = False  # since we need to build the image from scratch

    logger.info(f'Building image [{new_image_name}] from scratch')

    _build_sandbox_image(base_image, new_image_name, docker_client, skip_init=skip_init)
    return new_image_name


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--base_image', type=str, default='ubuntu:latest')
    parser.add_argument('--update_source_code', type=bool, default=False)
    args = parser.parse_args()

    client = docker.from_env()
    image_name = build_runtime_image(
        args.base_image, client, update_source_code=args.update_source_code
    )
    print(f'\nBUILT Image: {image_name}\n')
