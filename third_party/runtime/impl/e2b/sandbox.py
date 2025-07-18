import copy
import os
import tarfile
from glob import glob

from e2b import Sandbox as E2BSandbox
from e2b.exceptions import TimeoutException

from openhands.core.config import SandboxConfig
from openhands.core.logger import openhands_logger as logger


class E2BBox:
    closed = False
    _cwd: str = '/home/user'
    _env: dict[str, str] = {}
    is_initial_session: bool = True

    def __init__(
        self,
        config: SandboxConfig,
        template: str = 'openhands',
    ):
        self.config = copy.deepcopy(config)
        self.initialize_plugins: bool = config.initialize_plugins
        
        # Read API key from environment variable
        e2b_api_key = os.getenv('E2B_API_KEY')
        if not e2b_api_key:
            raise ValueError('E2B_API_KEY environment variable is required for E2B runtime')
        
        self.sandbox = E2BSandbox(
            api_key=e2b_api_key,
            template=template,
            # It's possible to stream stdout and stderr from sandbox and from each process
            on_stderr=lambda x: logger.debug(f'E2B sandbox stderr: {x}'),
            on_stdout=lambda x: logger.debug(f'E2B sandbox stdout: {x}'),
            cwd=self._cwd,  # Default workdir inside sandbox
        )
        logger.debug(f'Started E2B sandbox with ID "{self.sandbox.id}"')

    @property
    def filesystem(self):
        return self.sandbox.filesystem

    def _archive(self, host_src: str, recursive: bool = False):
        if recursive:
            assert os.path.isdir(host_src), (
                'Source must be a directory when recursive is True'
            )
            files = glob(host_src + '/**/*', recursive=True)
            srcname = os.path.basename(host_src)
            tar_filename = os.path.join(os.path.dirname(host_src), srcname + '.tar')
            with tarfile.open(tar_filename, mode='w') as tar:
                for file in files:
                    tar.add(
                        file, arcname=os.path.relpath(file, os.path.dirname(host_src))
                    )
        else:
            assert os.path.isfile(host_src), (
                'Source must be a file when recursive is False'
            )
            srcname = os.path.basename(host_src)
            tar_filename = os.path.join(os.path.dirname(host_src), srcname + '.tar')
            with tarfile.open(tar_filename, mode='w') as tar:
                tar.add(host_src, arcname=srcname)
        return tar_filename

    def execute(self, cmd: str, timeout: int | None = None) -> tuple[int, str]:
        timeout = timeout if timeout is not None else self.config.timeout
        process = self.sandbox.process.start(cmd, env_vars=self._env)
        try:
            process_output = process.wait(timeout=timeout)
        except TimeoutException:
            logger.debug('Command timed out, killing process...')
            process.kill()
            return -1, f'Command: "{cmd}" timed out'

        logs = [m.line for m in process_output.messages]
        logs_str = '\n'.join(logs)
        if process.exit_code is None:
            return -1, logs_str

        assert process_output.exit_code is not None
        return process_output.exit_code, logs_str

    def copy_to(self, host_src: str, sandbox_dest: str, recursive: bool = False):
        """Copies a local file or directory to the sandbox."""
        tar_filename = self._archive(host_src, recursive)

        # Prepend the sandbox destination with our sandbox cwd
        sandbox_dest = os.path.join(self._cwd, sandbox_dest.removeprefix('/'))

        with open(tar_filename, 'rb') as tar_file:
            # Upload the archive to /home/user (default destination that always exists)
            uploaded_path = self.sandbox.upload_file(tar_file)

            # Check if sandbox_dest exists. If not, create it.
            process = self.sandbox.process.start_and_wait(f'test -d {sandbox_dest}')
            if process.exit_code != 0:
                self.sandbox.filesystem.make_dir(sandbox_dest)

            # Extract the archive into the destination and delete the archive
            process = self.sandbox.process.start_and_wait(
                f'sudo tar -xf {uploaded_path} -C {sandbox_dest} && sudo rm {uploaded_path}'
            )
            if process.exit_code != 0:
                raise Exception(
                    f'Failed to extract {uploaded_path} to {sandbox_dest}: {process.stderr}'
                )

        # Delete the local archive
        os.remove(tar_filename)

    def close(self):
        self.sandbox.close()

    def get_working_directory(self):
        return self.sandbox.cwd


# Alias for backward compatibility
E2BSandbox = E2BBox
