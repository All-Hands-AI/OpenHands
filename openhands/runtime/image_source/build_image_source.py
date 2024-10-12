import hashlib
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional

from docker import DockerClient
from docker.models.images import Image
from jinja2 import Environment, FileSystemLoader

from openhands.core.logger import openhands_logger
from openhands.runtime.image_source.image_source_abc import ImageSourceABC
from openhands.utils.async_utils import wait_all
from openhands.utils.docker_utils import get_local_image, pull_image
from openhands.utils.file_hash import md5s_for_path


@dataclass
class BuildImageSource(ImageSourceABC):
    """
    Image source which builds a docker image from local files. Maintaining as much of the cached state as possible
    helps keep the build as fast as possible
    """

    base_image_name: str = field(default='nikolaik/python-nodejs:python3.12-nodejs22')
    sandbox_image_name_prefix: str = 'oh_sandbox_'
    cwd: str = field(default_factory=os.getcwd)
    extra_deps: Optional[str] = field(default=None)
    target_image_name: Optional[str] = field(default=None)
    target_image_tag: Optional[str] = field(default=None)
    docker_file: str = 'full_Dockerfile.j2'
    docker_client: DockerClient = field(default_factory=DockerClient.from_env)
    _image: Optional[Image] = None

    async def get_image(self) -> str:
        if self._image:
            return self._image
        image_name = await self.build_image_name()
        image = get_local_image(image_name, self.docker_client)
        if not image:
            image = await self.build_image(image_name)
        self._image = image
        return image.name + ':' + image.tags[0]

    async def build_image_name(self) -> str:
        md5s: Dict[Path, bytes] = {}
        root = Path(os.getcwd())
        await wait_all(
            md5s_for_path(path, compiled_filter, md5s) for path in root.iterdir()
        )
        hash = hashlib.md5()
        for path in sorted(md5s, key=lambda p: str(p)):
            hash.update(md5s[path])
        return self.sandbox_image_name_prefix + hash.hexdigest()

    async def build_image(self, image_name: str) -> Image:
        docker_client = self.docker_client
        base_image = get_local_image(self.base_image_name, docker_client)
        if not base_image:
            pull_image(self.base_image_name, docker_client)
            # Make sure image exists...
            docker_client.images.get(self.base_image_name)
        openhands_logger.info(f'building_docker_image:{image_name}')
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            self.build_project(temp_path)
            self.unzip_tarball(temp_path)
            self.create_dockerfile(temp_path)
            self.execute_docker_build(temp_path, image_name)
            image = docker_client.images.get(image_name)
            self.retag_image(image)
            return image

    def build_project(self, temp_path: Path):
        """
        Run a poetry build on the current project into the temp_path
        """
        result = subprocess.run(
            f"python -m build -s -o \"{temp_path}\" {self.cwd.replace(' ', r'\ ')}",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        openhands_logger.info(result.stdout.decode())
        err_logs = result.stderr.decode()
        if err_logs:
            openhands_logger.error(err_logs)
        if result.returncode != 0:
            openhands_logger.error(f'Image build failed:\n{result}')
            raise RuntimeError(f'Image build failed:\n{result}')

    def unzip_tarball(self, temp_path: Path):
        """
        Unzip the first available tarball in the directory given to a directory named "code".
        (Also remove the tarball)
        """
        try:
            tarball_path = next(
                p for p in temp_path.iterdir() if p.name.endswith('.tar.gz')
            )
        except StopIteration:
            openhands_logger.error(
                f'Source distribution not found at {temp_path}. (Do you need to run `make build`?)'
            )
        openhands_logger.info(f'Source distribution created at {tarball_path}')
        shutil.unpack_archive(tarball_path, temp_path)
        os.remove(tarball_path)
        code_path = next(p for p in temp_path.iterdir() if not p.name.startswith('.'))
        code_path.rename(Path(code_path.parent, 'code'))

    def create_dockerfile(self, temp_path: Path):
        """Create a dockerfile in the temp directory given."""
        env = Environment(
            loader=FileSystemLoader(
                searchpath=Path(Path(__file__).parent, 'dockerfile_templates')
            )
        )
        template = env.get_template(self.docker_file)
        dockerfile_content = template.render(
            base_image=self.base_image_name,
            extra_deps=self.extra_deps,
        )
        with open(Path(temp_path, 'Dockerfile'), 'w') as file:
            file.write(dockerfile_content)

    def execute_docker_build(self, temp_path: Path, image_name: str):
        buildx_cmd = [
            'docker',
            'buildx',
            'build',
            '--progress=plain',
            f'--tag={image_name}',
            '--load',
        ]

        # Cache args / extra build args were never used in openhands, so I did not copy those over

        buildx_cmd.append(str(temp_path))  # must be last!

        openhands_logger.info('building_docker_image:{image_name}')
        try:
            process = subprocess.Popen(
                buildx_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1,
            )

            if process.stdout:
                for line in iter(process.stdout.readline, ''):
                    line = line.strip()
                    if line:
                        openhands_logger.debug(line)

            return_code = process.wait()

            if return_code != 0:
                raise subprocess.CalledProcessError(
                    return_code,
                    process.args,
                    output=process.stdout.read() if process.stdout else None,
                    stderr=process.stderr.read() if process.stderr else None,
                )

        except subprocess.CalledProcessError as e:
            openhands_logger.error('Image build failed', exc_info=True)
            openhands_logger.error(f'Command output:\n{e.output}')
            raise
        except subprocess.TimeoutExpired:
            openhands_logger.error('Image build timed out', exc_info=True)
            raise
        except FileNotFoundError:
            openhands_logger.error('Python executable not found', exc_info=True)
            raise
        except PermissionError:
            openhands_logger.error('Build permission denied', exc_info=True)
            raise
        except Exception:
            openhands_logger.error(
                'An unexpected error occurred during the build process', exc_info=True
            )
            raise

        openhands_logger.info(f'Image [{image_name}] build finished.')

    def retag_image(self, image: Image):
        if self.target_image_tag:
            target_image_repo, target_image_tag = self.target_image_tag.split(':')
            image.tag(target_image_repo, target_image_tag)
            openhands_logger.info(
                f'Re-tagged image [{image.tags[0]}] with more generic tag [{self.target_image_tag}]'
            )


def compiled_filter(path: Path) -> bool:
    name = path.name
    if name.startswith('.') or name.endswith('.pyc') or name == '__pycache__':
        return False
    if path.is_dir() and not Path(path, '__init__.py').exists():
        return False
    return True
