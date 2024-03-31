from typing import Dict, List, Tuple
from opendevin.observation import CmdOutputObservation
# from opendevin.sandbox.sandbox import DockerInteractive
import concurrent.futures, os
from opendevin import config
import subprocess

RUN_AS_DEVIN = config.get_or_default("RUN_AS_DEVIN", "true").lower() != "false"

class BackgroundCommand:
    def __init__(self, id: int, command: str, result, pid: int):
        self.id = id
        self.command = command
        self.result = result
        self.pid = pid


class CommandManager:
    
    def __init__(self, dir: str, container_image: str | None = None,):
        self.directory = dir
        self.background_commands: Dict[int, BackgroundCommand] = {}
        # self.workspace_dir: dir
        self.timeout: int = 120
        self.id: str | None = None
        # x = self.workspace_dir
        
        # if isinstance(x, tuple) and len(x) == 1 and x[0] is notNone:
        #     os.makedirs(self.workspace_dir, exist_ok=True)
        #     # expand to absolute path
        #     self.workspace_dir = os.path.abspath(self.workspace_dir)
        # else:
        #     self.workspace_dir = os.getcwd()
        #     print(f"workspace unspecified, using current directory: {self.workspace_dir}")
    

        # self.shell = DockerInteractive(id="default", workspace_dir=dir, container_image=container_image)
        

    def run_command(self, command: str, background=False) -> CmdOutputObservation:
        return self.execute(command)

        # if background:
        #     return self._run_background(command)
        # else:
        #     return self._run_immediately(command)

    def execute(self, cmd: str) -> Tuple[int, str]:
        # TODO: each execute is not stateful! We need to keep track of the current working directory
        def run_command(container, command):
            return container.exec_run(command, self.directory)
        # Use ThreadPoolExecutor to control command and set timeout
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_command, self, self.get_exec_cmd(cmd))
            try:
                exit_code, logs = future.result(timeout=self.timeout)
            except concurrent.futures.TimeoutError:
                print("Command timed out, killing process...")
                pid = self.get_pid(cmd)
                if pid is not None:
                    self.exec_run(
                        f"kill -9 {pid}", workdir=self.directory
                    )
                return -1, f"Command: \"{cmd}\" timed out"
        return exit_code, logs.decode("utf-8")
    def get_exec_cmd(self, cmd: str) -> List[str]:
        if RUN_AS_DEVIN:
            return ["su", "appuser", "-c", cmd]
        else:
            return ["/bin/bash", "-c", cmd]
    def exec_run(self, cmd: str, socket=False, workdir=None):
        if RUN_AS_DEVIN:
            return subprocess.run(cmd, shell=True, cwd=workdir)

    def _run_background(self, command: str) -> CmdOutputObservation:
        bg_cmd = self.execute_in_background(command)
        return CmdOutputObservation(
            content=f"Background command started. To stop it, send a `kill` action with id {bg_cmd.id}",
            command_id=bg_cmd.id,
            command=command,
            exit_code=0
        )

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
            output = cmd.read_logs()
            if output is not None and output != "":
                obs.append(
                    CmdOutputObservation(
                        content=output, command_id=_id, command=cmd.command
                    )
                )
        return obs
    def execute(self, cmd: str) -> Tuple[int, str]:
        # TODO: each execute is not stateful! We need to keep track of the current working directory
        def run_command(self, command):
            return self.exec_run(command,self.directory)
        # Use ThreadPoolExecutor to control command and set timeout
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_command, self, self.get_exec_cmd(cmd))
            try:
                exit_code, logs = future.result(timeout=self.timeout)
# TypeError: cannot unpack non-iterable CompletedProcess object 
                               
            except concurrent.futures.TimeoutError:
                print("Command timed out, killing process...")
                pid = self.get_pid(cmd)
                if pid is not None:
                    self.exec_run(
                        f"kill -9 {pid}", self.directory
                    )
                return -1, f"Command: \"{cmd}\" timed out"
        return exit_code, logs.decode("utf-8")
    def execute_in_background(self, cmd: str) -> BackgroundCommand:
        result = self.exec_run(
            self.get_exec_cmd(cmd), socket=True, workdir=self.directory
        )
        result.output._sock.setblocking(0)
        pid = self.get_pid(cmd)
        bg_cmd = BackgroundCommand(self.cur_background_id, cmd, result, pid)
        self.background_commands[bg_cmd.id] = bg_cmd
        self.cur_background_id += 1
        return bg_cmd

    def get_pid(self, cmd):
        exec_result = self.exec_run("ps aux")
        processes = exec_result.output.decode('utf-8').splitlines()
        cmd = " ".join(self.get_exec_cmd(cmd))

        for process in processes:
            if cmd in process:
                pid = process.split()[1] # second column is the pid
                return pid
        return None

    def kill_background(self, id: int) -> BackgroundCommand:
        if id not in self.background_commands:
            raise ValueError("Invalid background command id")
        bg_cmd = self.background_commands[id]
        if bg_cmd.pid is not None:
            self.exec_run(
                f"kill -9 {bg_cmd.pid}", workdir=self.directory
            )
        bg_cmd.result.output.close()
        self.background_commands.pop(id)
        return bg_cmd

    # def close(self):
    #     self.stop_docker_container()
    #     self.closed = True

