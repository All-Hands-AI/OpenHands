import os
import shutil
import tempfile

import docker

from opendevin.core.logger import opendevin_logger as logger

from .source import create_project_source_dist


def generate_dockerfile(base_image: str) -> str:
    """
    Generate the Dockerfile content for the agnostic sandbox image based on user-provided base image.

    NOTE: This is only tested on debian yet.
    """
    # FIXME: Remove the requirement of ssh in future version
    dockerfile_content = (
        f'FROM {base_image}\n'
        'RUN apt update && apt install -y openssh-server wget sudo\n'
        'RUN mkdir -p -m0755 /var/run/sshd\n'
        'RUN mkdir -p /opendevin && mkdir -p /opendevin/logs && chmod 777 /opendevin/logs\n'
        'RUN echo "" > /opendevin/bash.bashrc\n'
        'RUN if [ ! -d /opendevin/miniforge3 ]; then \\\n'
        '        wget --progress=bar:force -O Miniforge3.sh "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh" && \\\n'
        '        bash Miniforge3.sh -b -p /opendevin/miniforge3 && \\\n'
        '        rm Miniforge3.sh && \\\n'
        '        chmod -R g+w /opendevin/miniforge3 && \\\n'
        '        bash -c ". /opendevin/miniforge3/etc/profile.d/conda.sh && conda config --set changeps1 False && conda config --append channels conda-forge"; \\\n'
        '    fi\n'
        'RUN /opendevin/miniforge3/bin/pip install --upgrade pip\n'
        'RUN /opendevin/miniforge3/bin/pip install jupyterlab notebook jupyter_kernel_gateway flake8\n'
        'RUN /opendevin/miniforge3/bin/pip install python-docx PyPDF2 python-pptx pylatexenc openai\n'
    ).strip()
    return dockerfile_content


def generate_dockerfile_for_eventstream_runtime(
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
    eventstream_runtime: bool = False,
    skip_init: bool = False,
):
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            if eventstream_runtime:
                dockerfile_content = generate_dockerfile_for_eventstream_runtime(
                    base_image, temp_dir, skip_init=skip_init
                )
            else:
                dockerfile_content = generate_dockerfile(base_image)

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


def _get_new_image_name(
    base_image: str, is_eventstream_runtime: bool, dev_mode: bool = False
) -> str:
    prefix = 'od_sandbox'
    if is_eventstream_runtime:
        prefix = 'od_eventstream_runtime'
    if dev_mode:
        prefix += '_dev'
    if ':' not in base_image:
        base_image = base_image + ':latest'

    [repo, tag] = base_image.split(':')
    repo = repo.replace('/', '___')
    return f'{prefix}:{repo}__{tag}'


def get_od_sandbox_image(
    base_image: str,
    docker_client: docker.DockerClient,
    is_eventstream_runtime: bool = False,
) -> str:
    """Return the sandbox image name based on user-provided base image.

    The returned sandbox image is assumed to contains all the required dependencies for OpenDevin.
    If the sandbox image is not found, it will be built.
    """
    # OpenDevin's offcial sandbox already contains the required dependencies for OpenDevin.
    if 'ghcr.io/opendevin/sandbox' in base_image:
        return base_image

    new_image_name = _get_new_image_name(base_image, is_eventstream_runtime)

    # Detect if the sandbox image is built
    image_exists = False
    images = docker_client.images.list()
    for image in images:
        if new_image_name in image.tags:
            logger.info('Found existing od_sandbox image, reuse:' + new_image_name)
            image_exists = True
            break

    skip_init = False
    if image_exists:
        if is_eventstream_runtime:
            # An eventstream runtime image is already built for the base image (with poetry and dev dependencies)
            # but it might not contain the latest version of the source code and dependencies.
            # So we need to build a new (dev) image with the latest source code and dependencies.
            # FIXME: In production, we should just build once (since the source code will not change)
            base_image = new_image_name
            new_image_name = _get_new_image_name(
                base_image, is_eventstream_runtime, dev_mode=True
            )

            # Delete the existing image named `new_image_name` if any
            images = docker_client.images.list()
            for image in images:
                if new_image_name in image.tags:
                    docker_client.images.remove(image.id, force=True)

            # We will reuse the existing image but will update the source code in it.
            skip_init = True
            logger.info(
                f'Reusing existing od_sandbox image [{base_image}] but will update the source code into [{new_image_name}]'
            )
        else:
            return new_image_name
    else:
        # If the sandbox image is not found, build it
        logger.info(
            f'od_sandbox image is not found for {base_image}, will build: {new_image_name}'
        )
    _build_sandbox_image(
        base_image,
        new_image_name,
        docker_client,
        is_eventstream_runtime,
        skip_init=skip_init,
    )
    return new_image_name
