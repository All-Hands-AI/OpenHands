#!/usr/bin/env python3
"""
Modified runtime_build.py that implements the PyInstaller approach.
"""

import argparse
import hashlib
import os
import shutil
import subprocess
import tempfile
from enum import Enum
from pathlib import Path

import docker
from jinja2 import Environment, FileSystemLoader

import openhands
from openhands import __version__ as oh_version
from openhands.core.exceptions import AgentRuntimeBuildError
from openhands.core.logger import openhands_logger as logger


class BuildMethod(Enum):
    PYINSTALLER = 'pyinstaller'  # Use PyInstaller to bundle the action_execution_server


def get_runtime_image_repo() -> str:
    return os.getenv('OH_RUNTIME_RUNTIME_IMAGE_REPO', 'ghcr.io/all-hands-ai/runtime')


def get_runtime_image_repo_and_tag(base_image: str) -> tuple[str, str]:
    """Retrieves the Docker repo and tag associated with the Docker image.

    Parameters:
    - base_image (str): The name of the base Docker image

    Returns:
    - tuple[str, str]: The Docker repo and tag of the Docker image
    """
    if get_runtime_image_repo() in base_image:
        logger.debug(
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
            repo = f"{repo[-24:]}_{repo_hash}"

        runtime_repo = get_runtime_image_repo()
        runtime_tag = f'oh_v{oh_version}_{tag}'
        return runtime_repo, runtime_tag


def _generate_dockerfile(
    base_image: str,
    build_method: BuildMethod = BuildMethod.PYINSTALLER,
) -> str:
    """Generate the Dockerfile content for the runtime image based on the base image.

    Parameters:
    - base_image (str): The base image provided for the runtime image
    - build_method (BuildMethod): The build method for the runtime image.

    Returns:
    - str: The resulting Dockerfile content
    """
    env = Environment(
        loader=FileSystemLoader(
            searchpath=os.path.join(os.path.dirname(__file__), 'openhands/runtime/utils/runtime_templates')
        )
    )

    template = env.get_template('Dockerfile.pyinstaller.j2')
    dockerfile_content = template.render(
        base_image=base_image,
    )

    return dockerfile_content


def build_pyinstaller_binary():
    """Build the PyInstaller binary for the action_execution_server."""
    logger.info("Building PyInstaller binary for action_execution_server...")
    
    # Check if poetry-pyinstaller-plugin is installed
    try:
        subprocess.run(["pip", "show", "poetry-pyinstaller-plugin"], check=True, capture_output=True)
        logger.info("Using poetry-pyinstaller-plugin to build the binary")
        
        # Build the binary using poetry
        subprocess.run(["poetry", "build", "--format", "pyinstaller"], check=True)
    except subprocess.CalledProcessError:
        logger.info("poetry-pyinstaller-plugin not found, using direct PyInstaller approach")
        
        # Build the binary using PyInstaller directly
        subprocess.run(["pyinstaller", "--onedir", "openhands/runtime/action_execution_server.py"], check=True)
        
        # Move the binary to the expected location
        os.makedirs("dist/pyinstaller", exist_ok=True)
        shutil.move("dist/action_execution_server", "dist/pyinstaller/action-execution-server")
    
    logger.info("PyInstaller binary built successfully")


def package_browser():
    """Package the Playwright browser for use with the PyInstaller binary."""
    logger.info("Packaging Playwright browser...")
    
    # Run the package_browser.py script
    subprocess.run(["python", "package_browser.py", "browser"], check=True)
    
    logger.info("Playwright browser packaged successfully")


def build_runtime_image(
    base_image: str,
    build_method: BuildMethod = BuildMethod.PYINSTALLER,
    no_cache: bool = False,
) -> str:
    """Build a runtime image based on the base image.

    Parameters:
    - base_image (str): The base image provided for the runtime image
    - build_method (BuildMethod): The build method for the runtime image.
    - no_cache (bool): Whether to use Docker cache when building the image

    Returns:
    - str: The name of the built runtime image
    """
    logger.info(f"Building runtime image with {build_method.value} method...")
    
    # Build the PyInstaller binary
    build_pyinstaller_binary()
    
    # Package the browser
    package_browser()
    
    # Generate the Dockerfile
    dockerfile_content = _generate_dockerfile(base_image, build_method)
    
    # Create a temporary directory for the Docker build context
    with tempfile.TemporaryDirectory() as tmpdir:
        # Write the Dockerfile to the temporary directory
        dockerfile_path = os.path.join(tmpdir, 'Dockerfile')
        with open(dockerfile_path, 'w') as f:
            f.write(dockerfile_content)
        
        # Copy the PyInstaller binary to the temporary directory
        shutil.copytree("dist/pyinstaller/action-execution-server", os.path.join(tmpdir, "dist/pyinstaller/action-execution-server"))
        
        # Copy the browser to the temporary directory
        shutil.copytree("browser", os.path.join(tmpdir, "browser"))
        
        # Get the runtime image name
        runtime_repo, runtime_tag = get_runtime_image_repo_and_tag(base_image)
        runtime_image = f"{runtime_repo}:{runtime_tag}"
        
        # Build the Docker image
        logger.info(f"Building Docker image {runtime_image}...")
        client = docker.from_env()
        try:
            client.images.build(
                path=tmpdir,
                tag=runtime_image,
                nocache=no_cache,
            )
            logger.info(f"Docker image {runtime_image} built successfully")
            return runtime_image
        except docker.errors.BuildError as e:
            logger.error(f"Error building Docker image: {e}")
            raise AgentRuntimeBuildError(f"Error building Docker image: {e}")


def main():
    """Main function for the runtime_build_pyinstaller.py script."""
    parser = argparse.ArgumentParser(description='Build a runtime image with PyInstaller')
    parser.add_argument('--base-image', type=str, default='ubuntu:22.04', help='Base image for the runtime')
    parser.add_argument('--no-cache', action='store_true', help='Do not use Docker cache when building the image')
    args = parser.parse_args()
    
    runtime_image = build_runtime_image(args.base_image, BuildMethod.PYINSTALLER, args.no_cache)
    print(f"Runtime image built: {runtime_image}")


if __name__ == '__main__':
    main()