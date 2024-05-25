import os
import tarfile
from glob import glob

from e2b import Sandbox as E2BSandbox
from e2b.sandbox.exception import (
    TimeoutException,
)

from opendevin.core.config import config
from opendevin.core.logger import opendevin_logger as logger
from opendevin.core.schema import CancellableStream
from opendevin.runtime.e2b.process import E2BProcess
from opendevin.runtime.process import Process
from opendevin.runtime.sandbox import Sandbox


class E2BBox(Sandbox):
    closed = False
    cur_background_id = 0
    background_commands: dict[int, Process] = {}
    _cwd: str = '/home/user'

    def __init__(
        self,
        template: str = 'open-devin',
        timeout: int = config.sandbox_timeout,
    ):
        self.sandbox = E2BSandbox(
            api_key=config.e2b_api_key,
            template=template,
            # It's possible to stream stdout and stderr from sandbox and from each process
            on_stderr=lambda x: logger.info(f'E2B sandbox stderr: {x}'),
            on_stdout=lambda x: logger.info(f'E2B sandbox stdout: {x}'),
            cwd=self._cwd,  # Default workdir inside sandbox
        )
        self.timeout = timeout
        logger.info(f'Started E2B sandbox with ID "{self.sandbox.id}"')
        super().__init__()

    @property
    def filesystem(self):
        return self.sandbox.filesystem

    def _archive(self, host_src: str, recursive: bool = False):
        if recursive:
            assert os.path.isdir(
                host_src
            ), 'Source must be a directory when recursive is True'
            files = glob(host_src + '/**/*', recursive=True)
            srcname = os.path.basename(host_src)
            tar_filename = os.path.join(os.path.dirname(host_src), srcname + '.tar')
            with tarfile.open(tar_filename, mode='w') as tar:
                for file in files:
                    tar.add(
                        file, arcname=os.path.relpath(file, os.path.dirname(host_src))
                    )
        else:
            assert os.path.isfile(
                host_src
            ), 'Source must be a file when recursive is False'
            srcname = os.path.basename(host_src)
            tar_filename = os.path.join(os.path.dirname(host_src), srcname + '.tar')
            with tarfile.open(tar_filename, mode='w') as tar:
                tar.add(host_src, arcname=srcname)
        return tar_filename

    # TODO: This won't work if we didn't wait for the background process to finish
    def read_logs(self, process_id: int) -> str:
        proc = self.background_commands.get(process_id)
        if proc is None:
            raise ValueError(f'Process {process_id} not found')
        assert isinstance(proc, E2BProcess)
        return '\n'.join([m.line for m in proc.output_messages])

    def execute(
        self, cmd: str, stream: bool = False, timeout: int | None = None
    ) -> tuple[int, str | CancellableStream]:
        timeout = timeout if timeout is not None else self.timeout
        process = self.sandbox.process.start(cmd, env_vars=self._env)
        try:
            process_output = process.wait(timeout=timeout)
        except TimeoutException:
            logger.info('Command timed out, killing process...')
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

    def execute_in_background(self, cmd: str) -> Process:
        process = self.sandbox.process.start(cmd)
        e2b_process = E2BProcess(process, cmd)
        self.cur_background_id += 1
        self.background_commands[self.cur_background_id] = e2b_process
        return e2b_process

    def kill_background(self, process_id: int):
        process = self.background_commands.get(process_id)
        if process is None:
            raise ValueError(f'Process {process_id} not found')
        assert isinstance(process, E2BProcess)
        process.kill()
        return process

    def close(self):
        self.sandbox.close()

    def get_working_directory(self):
        return self.sandbox.cwd
