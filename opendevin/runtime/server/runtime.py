from opendevin.core.config import config
from opendevin.events.action import (
    AgentRecallAction,
    BrowseInteractiveAction,
    BrowseURLAction,
    CmdKillAction,
    CmdRunAction,
    FileReadAction,
    FileWriteAction,
    IPythonRunCellAction,
)
from opendevin.events.observation import (
    CmdOutputObservation,
    ErrorObservation,
    IPythonRunCellObservation,
    NullObservation,
    Observation,
)
from opendevin.events.stream import EventStream
from opendevin.runtime import Sandbox
from opendevin.runtime.runtime import Runtime
from opendevin.storage.local import LocalFileStore

from .browse import browse
from .files import read_file, write_file


class ServerRuntime(Runtime):
    def __init__(
        self,
        event_stream: EventStream,
        sid: str = 'default',
        sandbox: Sandbox | None = None,
    ):
        super().__init__(event_stream, sid, sandbox)
        self.file_store = LocalFileStore(config.workspace_base)

    async def run(self, action: CmdRunAction) -> Observation:
        return self._run_command(action.command, background=action.background)

    async def kill(self, action: CmdKillAction) -> Observation:
        cmd = self.sandbox.kill_background(action.command_id)
        return CmdOutputObservation(
            content=f'Background command with id {action.command_id} has been killed.',
            command_id=action.command_id,
            command=cmd.command,
            exit_code=0,
        )

    async def run_ipython(self, action: IPythonRunCellAction) -> Observation:
        obs = self._run_command(
            ('cat > /tmp/opendevin_jupyter_temp.py <<EOL\n' f'{action.code}\n' 'EOL'),
            background=False,
        )

        # run the code
        obs = self._run_command(
            ('cat /tmp/opendevin_jupyter_temp.py | execute_cli'), background=False
        )
        output = obs.content
        if 'pip install' in action.code and 'Successfully installed' in output:
            print(output)
            restart_kernel = 'import IPython\nIPython.Application.instance().kernel.do_shutdown(True)'
            if (
                'Note: you may need to restart the kernel to use updated packages.'
                in output
            ):
                obs = self._run_command(
                    (
                        'cat > /tmp/opendevin_jupyter_temp.py <<EOL\n'
                        f'{restart_kernel}\n'
                        'EOL'
                    ),
                    background=False,
                )
                obs = self._run_command(
                    ('cat /tmp/opendevin_jupyter_temp.py | execute_cli'),
                    background=False,
                )
                output = '[Package installed successfully]'
                if "{'status': 'ok', 'restart': True}" != obs.content.strip():
                    print(obs.content)
                    output += '\n[But failed to restart the kernel to load the package]'
                else:
                    output += '\n[Kernel restarted successfully to load the package]'

                # re-init the kernel after restart
                if action.kernel_init_code:
                    obs = self._run_command(
                        (
                            f'cat > /tmp/opendevin_jupyter_init.py <<EOL\n'
                            f'{action.kernel_init_code}\n'
                            'EOL'
                        ),
                        background=False,
                    )
                    obs = self._run_command(
                        'cat /tmp/opendevin_jupyter_init.py | execute_cli',
                        background=False,
                    )

        return IPythonRunCellObservation(content=output, code=action.code)

    async def read(self, action: FileReadAction) -> Observation:
        # TODO: use self.file_store
        working_dir = self.sandbox.get_working_directory()
        return await read_file(action.path, working_dir, action.start, action.end)

    async def write(self, action: FileWriteAction) -> Observation:
        # TODO: use self.file_store
        working_dir = self.sandbox.get_working_directory()
        return await write_file(
            action.path, working_dir, action.content, action.start, action.end
        )

    async def browse(self, action: BrowseURLAction) -> Observation:
        return await browse(action, self.browser)

    async def browse_interactive(self, action: BrowseInteractiveAction) -> Observation:
        return await browse(action, self.browser)

    async def recall(self, action: AgentRecallAction) -> Observation:
        return NullObservation('')

    def _run_command(self, command: str, background=False) -> Observation:
        if background:
            return self._run_background(command)
        else:
            return self._run_immediately(command)

    def _run_immediately(self, command: str) -> Observation:
        try:
            exit_code, output = self.sandbox.execute(command)
            if 'pip install' in command and 'Successfully installed' in output:
                print(output)
                output = 'Package installed successfully'
            return CmdOutputObservation(
                command_id=-1, content=str(output), command=command, exit_code=exit_code
            )
        except UnicodeDecodeError:
            return ErrorObservation('Command output could not be decoded as utf-8')

    def _run_background(self, command: str) -> Observation:
        bg_cmd = self.sandbox.execute_in_background(command)
        content = f'Background command started. To stop it, send a `kill` action with command_id {bg_cmd.pid}'
        return CmdOutputObservation(
            content=content,
            command_id=bg_cmd.pid,
            command=command,
            exit_code=0,
        )
