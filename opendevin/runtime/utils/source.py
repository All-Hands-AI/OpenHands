import os
import subprocess
from importlib.metadata import version

import opendevin
from opendevin.core.logger import opendevin_logger as logger


def create_project_source_dist():
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
    logger.info(f'Source distribution create result: {result}')

    tarball_path = os.path.join(
        project_root, 'dist', f'opendevin-{version("opendevin")}.tar.gz'
    )
    if not os.path.exists(tarball_path):
        logger.error(f'Source distribution not found at {tarball_path}')
        raise Exception(f'Source distribution not found at {tarball_path}')
    logger.info(f'Source distribution created at {tarball_path}')

    return tarball_path
