import subprocess
import select
from typing import List

from opendevin.lib.event import Event
from opendevin.sandbox.sandbox import DockerInteractive

class BackgroundCommand:
    def __init__(self, id: int, command: str, dir: str):
        self.command = command
        self.id = id
        self.shell = DockerInteractive(id=str(id), workspace_dir=dir)
        self.shell.execute_in_background(command)

    def get_logs(self):
        # TODO: get an exit code if process is exited
        return self.shell.read_logs()

class CommandManager:
    def __init__(self, dir):
        self.cur_id = 0
        self.directory = dir
        self.background_commands = {}
        self.shell = DockerInteractive(id="default", workspace_dir=dir)

    def run_command(self, command: str, background=False) -> str:
        if background:
            return self.run_background(command)
        else:
            return self.run_immediately(command)

    def run_immediately(self, command: str) -> str:
        exit_code, output = self.shell.execute(command)
        if exit_code != 0:
            raise ValueError('Command failed with exit code ' + str(exit_code) + ': ' + output)
        return output

    def run_background(self, command: str) -> str:
        bg_cmd = BackgroundCommand(self.cur_id, command, self.directory)
        self.cur_id += 1
        self.background_commands[bg_cmd.id] = bg_cmd
        return "Background command started. To stop it, send a `kill` action with id " + str(bg_cmd.id)

    def kill_command(self, id: int) -> str:
        # TODO: get log events before killing
        self.background_commands[id].shell.close()
        del self.background_commands[id]

    def get_background_events(self) -> List[Event]:
        events = []
        for id, cmd in self.background_commands.items():
            output = cmd.get_logs()
            events.append(Event('output', {
                'output': output,
                'id': id,
                'command': cmd.command,
            }))
        return events
