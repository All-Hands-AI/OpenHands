import atexit
import os
import subprocess
import sys
from typing import Dict, Tuple

from opendevin.core import config
from opendevin.core.logger import opendevin_logger as logger
from opendevin.core.schema.config import ConfigType
from opendevin.runtime.docker.process import DockerProcess, Process
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
    def __init__(self, timeout: int = 120):
        os.makedirs(config.get(ConfigType.WORKSPACE_BASE), exist_ok=True)
        self.timeout = timeout
        self.background_commands: Dict[int, Process] = {}
        self.cur_background_id = 0
        atexit.register(self.cleanup)

    def execute(self, cmd: str) -> Tuple[int, str]:
        try:
            completed_process = subprocess.run(
                cmd,
                shell=True,
                text=True,
                capture_output=True,
                timeout=self.timeout,
                cwd=config.get(ConfigType.WORKSPACE_BASE),
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
            cwd=config.get(ConfigType.WORKSPACE_BASE),
        )
        if res.returncode != 0:
            raise RuntimeError(f'Failed to create directory {sandbox_dest} in sandbox')

        if recursive:
            res = subprocess.run(
                f'cp -r {host_src} {sandbox_dest}',
                shell=True,
                text=True,
                cwd=config.get(ConfigType.WORKSPACE_BASE),
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
                cwd=config.get(ConfigType.WORKSPACE_BASE),
            )
            if res.returncode != 0:
                raise RuntimeError(
                    f'Failed to copy {host_src} to {sandbox_dest} in sandbox'
                )

    def execute_in_background(self, cmd: str) -> Process:
        process = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=config.get(ConfigType.WORKSPACE_BASE),
        )
        bg_cmd = DockerProcess(
            id=self.cur_background_id, command=cmd, result=process, pid=process.pid
        )
        self.background_commands[self.cur_background_id] = bg_cmd
        self.cur_background_id += 1
        return bg_cmd

    def kill_background(self, id: int):
        if id not in self.background_commands:
            raise ValueError('Invalid background command id')
        bg_cmd = self.background_commands[id]
        assert isinstance(bg_cmd, DockerProcess)
        bg_cmd.result.terminate()  # terminate the process
        bg_cmd.result.wait()  # wait for process to terminate
        self.background_commands.pop(id)

    def read_logs(self, id: int) -> str:
        if id not in self.background_commands:
            raise ValueError('Invalid background command id')
        bg_cmd = self.background_commands[id]
        assert isinstance(bg_cmd, DockerProcess)
        output = bg_cmd.result.stdout.read()
        return output.decode('utf-8')

    def close(self):
        for id, bg_cmd in list(self.background_commands.items()):
            self.kill_background(id)

    def cleanup(self):
        self.close()

    def get_working_directory(self):
        return config.get(ConfigType.WORKSPACE_BASE)


if __name__ == '__main__':
    local_box = LocalBox()
    bg_cmd = local_box.execute_in_background(
        "while true; do echo 'dot ' && sleep 10; done"
    )

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
            if user_input.lower() == 'kill':
                local_box.kill_background(bg_cmd.pid)
                logger.info('Background process killed')
                continue
            exit_code, output = local_box.execute(user_input)
            logger.info('exit code: %d', exit_code)
            logger.info(output)
            if bg_cmd.pid in local_box.background_commands:
                logs = local_box.read_logs(bg_cmd.pid)
                logger.info('background logs: %s', logs)
            sys.stdout.flush()
    except KeyboardInterrupt:
        logger.info('Exiting...')
    local_box.close()
