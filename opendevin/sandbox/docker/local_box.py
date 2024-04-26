import subprocess
import atexit
import os
from typing import Tuple, Dict
from opendevin.sandbox.sandbox import Sandbox
from opendevin.sandbox.process import Process
from opendevin.sandbox.docker.process import DockerProcess
from opendevin import config
from opendevin.schema.config import ConfigType

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
                cmd, shell=True, text=True, capture_output=True,
                timeout=self.timeout, cwd=config.get('WORKSPACE_BASE')
            )
            return completed_process.returncode, completed_process.stdout.strip()
        except subprocess.TimeoutExpired:
            return -1, 'Command timed out'

    def copy_to(self, host_src: str, sandbox_dest: str, recursive: bool = False):
        # mkdir -p sandbox_dest if it doesn't exist
        res = subprocess.run(f'mkdir -p {sandbox_dest}', shell=True, text=True, cwd=config.get('WORKSPACE_BASE'))
        if res.returncode != 0:
            raise RuntimeError(f'Failed to create directory {sandbox_dest} in sandbox')

        if recursive:
            res = subprocess.run(
                f'cp -r {host_src} {sandbox_dest}', shell=True, text=True, cwd=config.get('WORKSPACE_BASE')
            )
            if res.returncode != 0:
                raise RuntimeError(f'Failed to copy {host_src} to {sandbox_dest} in sandbox')
        else:
            res = subprocess.run(
                f'cp {host_src} {sandbox_dest}', shell=True, text=True, cwd=config.get('WORKSPACE_BASE')
            )
            if res.returncode != 0:
                raise RuntimeError(f'Failed to copy {host_src} to {sandbox_dest} in sandbox')

    def execute_in_background(self, cmd: str) -> Process:
        process = subprocess.Popen(
            cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, cwd=config.get('WORKSPACE_BASE')
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
