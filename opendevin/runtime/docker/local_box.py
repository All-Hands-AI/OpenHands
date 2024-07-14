import asyncio
import atexit
import os
import subprocess
import sys

from opendevin.core.config import config
from opendevin.core.logger import opendevin_logger as logger
from opendevin.core.schema import CancellableStream
from opendevin.runtime.sandbox import Sandbox
from opendevin.runtime.utils.async_utils import async_to_sync

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
    _instance = None
    _initialization_lock = asyncio.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, timeout: int = config.sandbox.timeout):
        if not hasattr(self, '_initialized'):
            os.makedirs(config.workspace_base, exist_ok=True)
            self.timeout = timeout
            self._env = os.environ.copy()
            self._initialized = False
            self._local_init_complete = asyncio.Event()
            atexit.register(self.sync_cleanup)
            super().__init__()

    @async_to_sync
    def initialize(self):
        return self.ainit()

    async def ainit(self):
        await super().initialize()
        if not self._local_init_complete.is_set():
            async with self._initialization_lock:
                if not self._local_init_complete.is_set():
                    logger.info('Initializing LocalBox')
                    try:
                        await self._setup_environment()
                        # any other init code
                        self._initialized = True
                        logger.info('LocalBox initialization complete')
                    finally:
                        self._local_init_complete.set()
        else:
            await self._local_init_complete.wait()

    async def _setup_environment(self):
        # Set up any necessary environment variables or configurations
        for key, value in os.environ.items():
            if key.startswith('SANDBOX_ENV_'):
                sandbox_key = key.removeprefix('SANDBOX_ENV_')
                if sandbox_key:
                    await self.add_to_env_async(sandbox_key, value)

        # Change to the workspace directory
        os.chdir(config.workspace_base)
        self._env['PWD'] = config.workspace_base

    @async_to_sync
    def execute(
        self, cmd: str, stream: bool = False, timeout: int | None = None
    ) -> tuple[int, str | CancellableStream]:
        return self.execute_async(cmd, stream, timeout)  # type: ignore

    async def execute_async(
        self, cmd: str, stream: bool = False, timeout: int | None = None
    ) -> tuple[int, str | CancellableStream]:
        timeout = timeout if timeout is not None else self.timeout
        try:
            # Run the subprocess in a separate thread to avoid blocking the event loop
            process = await asyncio.to_thread(
                subprocess.run,
                cmd,
                shell=True,
                text=True,
                capture_output=True,
                timeout=timeout,
                cwd=config.workspace_base,
                env=self._env,
            )
            return process.returncode, process.stdout.strip()
        except subprocess.TimeoutExpired:
            return -1, 'Command timed out'

    @async_to_sync
    def copy_to(self, host_src: str, sandbox_dest: str, recursive: bool = False):
        return self.copy_to_async(host_src, sandbox_dest, recursive)

    async def copy_to_async(
        self, host_src: str, sandbox_dest: str, recursive: bool = False
    ):
        # mkdir -p sandbox_dest if it doesn't exist
        mkdir_cmd = f'mkdir -p {sandbox_dest}'
        exit_code, _ = await self.execute_async(mkdir_cmd)
        if exit_code != 0:
            raise RuntimeError(f'Failed to create directory {sandbox_dest} in sandbox')

        cp_cmd = (
            f'cp -r {host_src} {sandbox_dest}'
            if recursive
            else f'cp {host_src} {sandbox_dest}'
        )
        exit_code, _ = await self.execute_async(cp_cmd)
        if exit_code != 0:
            raise RuntimeError(
                f'Failed to copy {host_src} to {sandbox_dest} in sandbox'
            )

    @async_to_sync
    def add_to_env(self, key: str, value: str):
        return self.add_to_env_async(key, value)

    async def add_to_env_async(self, key: str, value: str):
        self._env[key] = value
        os.environ[key] = value

    async def get_working_directory(self):
        return config.workspace_base

    @async_to_sync
    def close(self):
        return self.aclose()

    async def aclose(self):
        # Perform any necessary async cleanup here
        pass

    def cleanup(self):
        # Perform any necessary synchronous cleanup here
        pass

    def __del__(self):
        self.cleanup()

    def sync_cleanup(self):
        pass


if __name__ == '__main__':
    local_box = LocalBox()
    sys.stdout.flush()

    async def main():
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
                exit_code, output = await local_box.execute(user_input)
                logger.info('exit code: %d', exit_code)
                logger.info(output)
                sys.stdout.flush()
        except KeyboardInterrupt:
            logger.info('Exiting...')
        await local_box.close()

    asyncio.run(main())
