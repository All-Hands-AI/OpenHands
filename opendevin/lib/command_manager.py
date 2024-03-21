import subprocess
import select
from typing import List

from opendevin.lib.event import Event

class BackgroundCommand:
    def __init__(self, id: int, command: str, process: subprocess.Popen):
        self.command = command
        self.id = id
        self.process = process

    def _get_log_from_stream(self, stream):
        logs = ""
        while True:
            readable, _, _ = select.select([stream], [], [], .1)
            if not readable:
                break
            next = stream.readline()
            if next == '':
                break
            logs += next
        if logs == "": return
        return logs

    def get_logs(self):
        stdout = self._get_log_from_stream(self.process.stdout)
        stderr = self._get_log_from_stream(self.process.stderr)
        exit_code = self.process.poll()
        return stdout, stderr, exit_code

class CommandManager:
    def __init__(self):
        self.cur_id = 0
        self.background_commands = {}

    def run_command(self, command: str, background=False) -> str:
        if background:
            return self.run_background(command)
        else:
            return self.run_immediately(command)

    def run_immediately(self, command: str) -> str:
        result = subprocess.run(["/bin/bash", "-c", command], capture_output=True, text=True)
        output = result.stdout + result.stderr
        exit_code = result.returncode
        if exit_code != 0:
            raise ValueError('Command failed with exit code ' + str(exit_code) + ': ' + output)
        return output

    def run_background(self, command: str) -> str:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
        bg_cmd = BackgroundCommand(self.cur_id, command, process)
        self.cur_id += 1
        self.background_commands[bg_cmd.id] = bg_cmd
        return "Background command started. To stop it, send a `kill` action with id " + str(bg_cmd.id)

    def kill_command(self, id: int) -> str:
        # TODO: get log events before killing
        self.background_commands[id].processs.kill()
        del self.background_commands[id]

    def get_background_events(self) -> List[Event]:
        events = []
        for id, cmd in self.background_commands.items():
            stdout, stderr, exit_code = cmd.get_logs()
            if stdout is not None:
                events.append(Event('output', {
                    'output': stdout,
                    'stream': 'stdout',
                    'id': id,
                    'command': cmd.command,
                }))
            if stderr is not None:
                events.append(Event('output', {
                    'output': stderr,
                    'stream': 'stderr',
                    'id': id,
                    'command': cmd.command,
                }))
            if exit_code is not None:
                events.append(Event('output', {
                    'exit_code': exit_code,
                    'output': 'Background command %d exited with code %d' % (idx, exit_code),
                    'id': id,
                    'command': cmd.command,
                }))
                del self.background_commands[id]
        return events
