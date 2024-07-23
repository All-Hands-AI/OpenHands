import atexit
import os
import subprocess
import sys

from opendevin.core.config import SandboxConfig
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
    def __init__(
        self,
        config: SandboxConfig,
        workspace_base: str,
    ):
        self.config = config
        os.makedirs(workspace_base, exist_ok=True)
        self.workspace_base = workspace_base
        atexit.register(self.cleanup)
        super().__init__(config)

    def execute(
        self, cmd: str, stream: bool = False, timeout: int | None = None
    ) -> tuple[int, str | CancellableStream]:
        try:
            completed_process = subprocess.run(
                cmd,
                shell=True,
                text=True,
                capture_output=True,
                timeout=self.config.timeout,
                cwd=self.workspace_base,
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
            cwd=self.workspace_base,
            env=self._env,
        )
        if res.returncode != 0:
            raise RuntimeError(f'Failed to create directory {sandbox_dest} in sandbox')

        if recursive:
            res = subprocess.run(
                f'cp -r {host_src} {sandbox_dest}',
                shell=True,
                text=True,
                cwd=self.workspace_base,
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
                cwd=self.workspace_base,
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
        return self.workspace_base


if __name__ == '__main__':
    local_box = LocalBox(SandboxConfig(), '/tmp/opendevin')
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
