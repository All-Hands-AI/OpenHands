import atexit
import os
import subprocess
import sys

from opendevin.core.config import config
from opendevin.core.logger import opendevin_logger as logger
from opendevin.core.schema import CancellableStream
from opendevin.runtime.sandbox import Sandbox

# ===============================================================================
#  ** WARNING **
#
#  This sandbox should only be used when OpenDevin is running inside a container
#
#  Sandboxes are generally isolated so that they cannot affect the host machine.
#  This Sandbox implementation does not provide isolation, and can inadvertently
#  run dangerous commands on the host machine, potentially rendering the host
#  machine unusable.
#
#  This sandbox is meant for use with OpenDevin Quickstart
#
#  DO NOT USE THIS SANDBOX IN A PRODUCTION ENVIRONMENT
# ===============================================================================


class LocalBox(Sandbox):
    def __init__(self, timeout: int = config.sandbox.timeout):
        os.makedirs(config.workspace_base, exist_ok=True)
        self.timeout = timeout
        atexit.register(self.cleanup)
        super().__init__()

    def execute(
        self, cmd: str, stream: bool = False, timeout: int | None = None
    ) -> tuple[int, str | CancellableStream]:
        timeout = timeout if timeout is not None else self.timeout
        try:
            completed_process = subprocess.run(
                cmd,
                shell=True,
                text=True,
                capture_output=True,
                timeout=timeout,
                cwd=config.workspace_base,
                env=self._env,
            )
            return completed_process.returncode, completed_process.stdout.strip()
        except subprocess.TimeoutExpired:
            return -1, 'Command timed out'

    def copy_to(self, host_src: str, sandbox_dest: str, recursive: bool = False):
        # mkdir -p sandbox_dest if it doesn't exist
        res = subprocess.run(
            f'mkdir -p {sandbox_dest}',
            shell=True,
            text=True,
            cwd=config.workspace_base,
            env=self._env,
        )
        if res.returncode != 0:
            raise RuntimeError(f'Failed to create directory {sandbox_dest} in sandbox')

        if recursive:
            res = subprocess.run(
                f'cp -r {host_src} {sandbox_dest}',
                shell=True,
                text=True,
                cwd=config.workspace_base,
                env=self._env,
            )
            if res.returncode != 0:
                raise RuntimeError(
                    f'Failed to copy {host_src} to {sandbox_dest} in sandbox'
                )
        else:
            res = subprocess.run(
                f'cp {host_src} {sandbox_dest}',
                shell=True,
                text=True,
                cwd=config.workspace_base,
                env=self._env,
            )
            if res.returncode != 0:
                raise RuntimeError(
                    f'Failed to copy {host_src} to {sandbox_dest} in sandbox'
                )

    def close(self):
        pass

    def cleanup(self):
        self.close()

    def get_working_directory(self):
        return config.workspace_base


if __name__ == '__main__':
    local_box = LocalBox()
    sys.stdout.flush()
    try:
        while True:
            try:
                user_input = input('>>> ')
            except EOFError:
                logger.info('Exiting...')
                break
            if user_input.lower() == 'exit':
                logger.info('Exiting...')
                break
            exit_code, output = local_box.execute(user_input)
            logger.info('exit code: %d', exit_code)
            logger.info(output)
            sys.stdout.flush()
    except KeyboardInterrupt:
        logger.info('Exiting...')
    local_box.close()
