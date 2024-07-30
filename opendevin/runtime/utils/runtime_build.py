import argparse
import os
import shutil
import subprocess
import tempfile

import docker
import toml
from jinja2 import Environment, FileSystemLoader

import opendevin
from opendevin.core.logger import opendevin_logger as logger


def _get_package_version():
    """Read the version from pyproject.toml as the other one may be outdated."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(opendevin.__file__)))
    pyproject_path = os.path.join(project_root, 'pyproject.toml')
    with open(pyproject_path, 'r') as f:
        pyproject_data = toml.load(f)
    return pyproject_data['tool']['poetry']['version']


def _create_project_source_dist():
    """Create a source distribution of the project. Return the path to the tarball."""
    # Copy the project directory to the container
    # get the location of "opendevin" package
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(opendevin.__file__)))
    logger.info(f'Using project root: {project_root}')

    # run "python -m build -s" on project_root
    result = subprocess.run(['python', '-m', 'build', '-s', project_root])
    if result.returncode != 0:
        logger.error(f'Build failed: {result}')
        raise Exception(f'Build failed: {result}')

    # Fetch the correct version from pyproject.toml
    package_version = _get_package_version()
    tarball_path = os.path.join(
        project_root, 'dist', f'opendevin-{package_version}.tar.gz'
    )
    if not os.path.exists(tarball_path):
        logger.error(f'Source distribution not found at {tarball_path}')
        raise Exception(f'Source distribution not found at {tarball_path}')
    logger.info(f'Source distribution created at {tarball_path}')

    return tarball_path


def _put_source_code_to_dir(temp_dir: str) -> str:
    tarball_path = _create_project_source_dist()
    filename = os.path.basename(tarball_path)
    filename = filename.removesuffix('.tar.gz')

    # move the tarball to temp_dir
    _res = shutil.copy(tarball_path, os.path.join(temp_dir, 'project.tar.gz'))
    if _res:
        os.remove(tarball_path)
    logger.info(
        f'Source distribution moved to {os.path.join(temp_dir, "project.tar.gz")}'
    )
    return filename


def _generate_dockerfile(
    base_image: str, source_code_dirname: str, skip_init: bool = False
) -> str:
    """Generate the Dockerfile content for the eventstream runtime image based on user-provided base image."""
    env = Environment(
        loader=FileSystemLoader(
            searchpath=os.path.join(os.path.dirname(__file__), 'runtime_templates')
        )
    )
    template = env.get_template('Dockerfile.j2')
    dockerfile_content = template.render(
        base_image=base_image,
        source_code_dirname=source_code_dirname,
        skip_init=skip_init,
    )
    return dockerfile_content


def prep_docker_build_folder(
    dir_path: str,
    base_image: str,
    skip_init: bool = False,
):
    """Prepares the docker build folder by copying the source code and generating the Dockerfile."""
    source_code_dirname = _put_source_code_to_dir(dir_path)
    dockerfile_content = _generate_dockerfile(
        base_image, source_code_dirname, skip_init=skip_init
    )
    logger.info(
        (
            f'===== Dockerfile content =====\n'
            f'{dockerfile_content}\n'
            f'==============================='
        )
    )
    with open(os.path.join(dir_path, 'Dockerfile'), 'w') as file:
        file.write(dockerfile_content)


def _build_sandbox_image(
    base_image: str,
    target_image_name: str,
    docker_client: docker.DockerClient,
    skip_init: bool = False,
):
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            if skip_init:
                logger.info(
                    f'Reusing existing od_sandbox image [{target_image_name}] but will update the source code in it.'
                )
            else:
                logger.info(f'Building agnostic sandbox image: {target_image_name}')
            prep_docker_build_folder(temp_dir, base_image, skip_init=skip_init)
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

        # check if the image is built successfully
        image = docker_client.images.get(target_image_name)
        if image is None:
            raise RuntimeError(f'Build failed: Image {target_image_name} not found')
        logger.info(f'Image {target_image_name} built successfully')
    except docker.errors.BuildError as e:
        logger.error(f'Sandbox image build failed: {e}')
        raise e


def get_new_image_name(base_image: str, dev_mode: bool = False) -> str:
    if dev_mode:
        if 'od_runtime' not in base_image:
            raise ValueError(
                f'Base image {base_image} must be a valid od_runtime image to be used for dev mode.'
            )
        # remove the 'od_runtime' prefix from the base_image
        return base_image.replace('od_runtime', 'od_runtime_dev')
    elif 'od_runtime' in base_image:
        # if the base image is a valid od_runtime image, we will use it as is
        logger.info(f'Using existing od_runtime image [{base_image}]')
        return base_image
    else:
        prefix = 'od_runtime'
        if ':' not in base_image:
            base_image = base_image + ':latest'
        [repo, tag] = base_image.split(':')
        repo = repo.replace('/', '___')

        od_version = _get_package_version()
        return f'{prefix}:od_v{od_version}_image_{repo}_tag_{tag}'


def _check_image_exists(image_name: str, docker_client: docker.DockerClient) -> bool:
    images = docker_client.images.list()
    if images:
        for image in images:
            if image_name in image.tags:
                return True
    return False


def build_runtime_image(
    base_image: str,
    docker_client: docker.DockerClient,
    update_source_code: bool = False,
    save_to_local_store: bool = False,  # New parameter to control saving to local store
) -> str:
    """Build the runtime image for the OpenDevin runtime.

    This is only used for **eventstream runtime**.
    """
    new_image_name = get_new_image_name(base_image)
    if base_image == new_image_name:
        logger.info(
            f'Using existing od_runtime image [{base_image}]. Will NOT build a new image.'
        )
    else:
        logger.info(f'New image name: {new_image_name}')

    # Ensure new_image_name contains a colon
    if ':' not in new_image_name:
        raise ValueError(
            f'Invalid image name: {new_image_name}. Expected format "repository:tag".'
        )

    # Try to pull the new image from the registry
    try:
        docker_client.images.pull(new_image_name)
    except Exception:
        logger.info(f'Cannot pull image {new_image_name} directly')

    # Detect if the sandbox image is built
    image_exists = _check_image_exists(new_image_name, docker_client)
    if image_exists:
        logger.info(f'Image {new_image_name} exists')
    else:
        logger.info(f'Image {new_image_name} does not exist')

    skip_init = False
    if image_exists and not update_source_code:
        # If (1) Image exists & we are not updating the source code, we can reuse the existing production image
        logger.info('No image build done (not updating source code)')
        return new_image_name
    elif image_exists and update_source_code:
        # If (2) Image exists & we plan to update the source code (in dev mode), we need to rebuild the image
        # and give it a special name
        # e.g., od_runtime:ubuntu_tag_latest -> od_runtime_dev:ubuntu_tag_latest
        logger.info('Image exists, but updating source code requested')
        base_image = new_image_name
        new_image_name = get_new_image_name(base_image, dev_mode=True)

        skip_init = True  # since we only need to update the source code
    else:
        # If (3) Image does not exist, we need to build it from scratch
        # e.g., ubuntu:latest -> od_runtime:ubuntu_tag_latest
        # This snippet would allow to load from archive:
        # tar_path = f'{new_image_name.replace(":", "_")}.tar'
        # if os.path.exists(tar_path):
        #     logger.info(f'Loading image from {tar_path}')
        #     load_command = ['docker', 'load', '-i', tar_path]
        #     subprocess.run(load_command, check=True)
        #     logger.info(f'Image {new_image_name} loaded from {tar_path}')
        #     return new_image_name
        skip_init = False

    if not skip_init:
        logger.info(f'Building image [{new_image_name}] from scratch')

    _build_sandbox_image(base_image, new_image_name, docker_client, skip_init=skip_init)

    # Only for development: allow to save image as archive:
    if not image_exists and save_to_local_store:
        tar_path = f'{new_image_name.replace(":", "_")}.tar'
        save_command = ['docker', 'save', '-o', tar_path, new_image_name]
        subprocess.run(save_command, check=True)
        logger.info(f'Image saved to {tar_path}')

        load_command = ['docker', 'load', '-i', tar_path]
        subprocess.run(load_command, check=True)
        logger.info(f'Image {new_image_name} loaded back into Docker from {tar_path}')

    return new_image_name


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--base_image', type=str, default='ubuntu:22.04')
    parser.add_argument('--update_source_code', action='store_true')
    parser.add_argument('--save_to_local_store', action='store_true')
    parser.add_argument('--build_folder', type=str, default=None)
    args = parser.parse_args()

    if args.build_folder is not None:
        build_folder = args.build_folder
        assert os.path.exists(
            build_folder
        ), f'Build folder {build_folder} does not exist'
        logger.info(
            f'Will prepare a build folder by copying the source code and generating the Dockerfile: {build_folder}'
        )
        new_image_path = get_new_image_name(args.base_image)
        prep_docker_build_folder(
            build_folder, args.base_image, skip_init=args.update_source_code
        )
        new_image_name, new_image_tag = new_image_path.split(':')
        with open(os.path.join(build_folder, 'config.sh'), 'a') as file:
            file.write(
                (
                    f'DOCKER_IMAGE={new_image_name}\n'
                    f'DOCKER_IMAGE_TAG={new_image_tag}\n'
                )
            )
        logger.info(
            f'`config.sh` is updated with the new image name [{new_image_name}] and tag [{new_image_tag}]'
        )
        logger.info(f'Dockerfile and source distribution are ready in {build_folder}')
    else:
        logger.info('Building image in a temporary folder')
        client = docker.from_env()
        image_name = build_runtime_image(
            args.base_image,
            client,
            update_source_code=args.update_source_code,
            save_to_local_store=args.save_to_local_store,
        )
        print(f'\nBUILT Image: {image_name}\n')
