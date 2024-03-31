from typing import Dict, List, Tuple
from opendevin.observation import CmdOutputObservation
import subprocess
import concurrent.futures
import os

RUN_AS_DEVIN = True  # Assuming we want to run commands as 'devin' user

class BackgroundCommand:
    def __init__(self, id: int, command: str, result, pid: int):
        self.id = id
        self.command = command
        self.result = result
        self.pid = pid

class CommandManager:
    def __init__(self, dir: str, container_image: str | None = None):
        self.directory = dir
        self.background_commands: Dict[int, BackgroundCommand] = {}
        self.timeout = 120  # Timeout in seconds
        self.cur_background_id = 0

    def run_command(self, command: str, background=False) -> CmdOutputObservation:
        if background:
            return self._run_background(command)
        else:
            return self._run_immediately(command)

    def _run_immediately(self, command: str) -> CmdOutputObservation:
        exit_code, output = self.execute(command)
        return CmdOutputObservation(
            command_id=-1,
            content=output,
            command=command,
            exit_code=exit_code
        )

    def _run_background(self, command: str) -> CmdOutputObservation:
        bg_cmd = self.execute_in_background(command)
        return CmdOutputObservation(
            content=f"Background command started. To stop it, send a `kill` action with id {bg_cmd.id}",
            command_id=bg_cmd.id,
            command=command,
            exit_code=0
        )

    def execute(self, cmd: str) -> Tuple[int, str]:
        def run_command(command):
            return self.exec_run(command, self.directory)

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_command, self.get_exec_cmd(cmd))
            try:
                exit_code, logs = future.result(timeout=self.timeout)
            except concurrent.futures.TimeoutError:
                print("Command timed out, killing process...")
                pid = self.get_pid(cmd)
                if pid is not None:
                    self.exec_run(f"kill -9 {pid}", self.directory)
                return -1, f"Command: \"{cmd}\" timed out"
        return exit_code, logs.decode("utf-8")

    def get_exec_cmd(self, cmd: str) -> List[str]:
        if RUN_AS_DEVIN:
            return ["su", "devin", "-c", cmd]
        else:
            return ["/bin/bash", "-c", cmd]

    def exec_run(self, cmd: str, workdir: str):
        if RUN_AS_DEVIN:
            return subprocess.run(cmd, shell=True, cwd=workdir, capture_output=True)
        else:
            return subprocess.run(cmd, shell=True, cwd=workdir, capture_output=True)

    def execute_in_background(self, cmd: str) -> BackgroundCommand:
        result = self.exec_run(self.get_exec_cmd(cmd), self.directory)
        pid = self.get_pid(cmd)
        bg_cmd = BackgroundCommand(self.cur_background_id, cmd, result, pid)
        self.background_commands[bg_cmd.id] = bg_cmd
        self.cur_background_id += 1
        return bg_cmd

    def get_pid(self, cmd):
        exec_result = self.exec_run("ps aux", self.directory)
        processes = exec_result.stdout.decode('utf-8').splitlines()
        cmd = " ".join(self.get_exec_cmd(cmd))

        for process in processes:
            if cmd in process:
                pid = process.split()[1]  # second column is the pid
                return pid
        return None

    def kill_command(self, id: int) -> CmdOutputObservation:
        cmd = self.kill_background(id)
        return CmdOutputObservation(
            content=f"Background command with id {id} has been killed.",
            command_id=id,
            command=cmd.command,
            exit_code=0
        )

    def get_background_obs(self) -> List[CmdOutputObservation]:
        obs = []
        for _id, cmd in self.background_commands.items():
            output = cmd.result.stdout.decode("utf-8")
            if output:
                obs.append(
                    CmdOutputObservation(
                        content=output, command_id=_id, command=cmd.command
                    )
                )
        return obs

    def kill_background(self, id: int) -> BackgroundCommand:
        if id not in self.background_commands:
            raise ValueError("Invalid background command id")
        bg_cmd = self.background_commands[id]
        if bg_cmd.pid is not None:
            self.exec_run(f"kill -9 {bg_cmd.pid}", self.directory)
        self.background_commands.pop(id)
        return bg_cmd