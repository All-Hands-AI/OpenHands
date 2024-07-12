from typing import Any, Optional

from opendevin.core.config import config
from opendevin.core.exceptions import BrowserInitException
from opendevin.core.logger import opendevin_logger as logger
from opendevin.events.action import (
    BrowseInteractiveAction,
    BrowseURLAction,
    CmdRunAction,
    FileReadAction,
    FileWriteAction,
    IPythonRunCellAction,
)
from opendevin.events.observation import (
    CmdOutputObservation,
    ErrorObservation,
    IPythonRunCellObservation,
    Observation,
)
from opendevin.events.stream import EventStream
from opendevin.runtime import (
    DockerSSHBox,
    E2BBox,
    LocalBox,
    Sandbox,
)
from opendevin.runtime.browser.browser_env import BrowserEnv
from opendevin.runtime.plugins import PluginRequirement
from opendevin.runtime.runtime import Runtime
from opendevin.runtime.tools import RuntimeTool
from opendevin.storage.local import LocalFileStore

from ..browser import browse
from .files import read_file, write_file


def create_sandbox(sid: str = 'default', box_type: str = 'ssh') -> Sandbox:
    if box_type == 'local':
        return LocalBox()
    elif box_type == 'ssh':
        return DockerSSHBox(sid=sid)
    elif box_type == 'e2b':
        return E2BBox()
    else:
        raise ValueError(f'Invalid sandbox type: {box_type}')


class ServerRuntime(Runtime):
    def __init__(
        self,
        event_stream: EventStream,
        sid: str = 'default',
        sandbox: Sandbox | None = None,
    ):
        super().__init__(event_stream, sid)
        self.file_store = LocalFileStore(config.workspace_base)
        if sandbox is None:
            self.sandbox = create_sandbox(sid, config.sandbox.box_type)
            self._is_external_sandbox = False
        else:
            self.sandbox = sandbox
            self._is_external_sandbox = True
        self.browser: BrowserEnv | None = None

    async def ainit(self) -> None:
        pass

    async def close(self):
        if not self._is_external_sandbox:
            self.sandbox.close()
        if self.browser is not None:
            self.browser.close()

    def init_sandbox_plugins(self, plugins: list[PluginRequirement]) -> None:
        self.sandbox.init_plugins(plugins)

    def init_runtime_tools(
        self,
        runtime_tools: list[RuntimeTool],
        runtime_tools_config: Optional[dict[RuntimeTool, Any]] = None,
        is_async: bool = True,
    ) -> None:
        # if browser in runtime_tools, init it
        if RuntimeTool.BROWSER in runtime_tools:
            if runtime_tools_config is None:
                runtime_tools_config = {}
            browser_env_config = runtime_tools_config.get(RuntimeTool.BROWSER, {})
            try:
                self.browser = BrowserEnv(is_async=is_async, **browser_env_config)
            except BrowserInitException:
                logger.warn(
                    'Failed to start browser environment, web browsing functionality will not work'
                )

    async def run(self, action: CmdRunAction) -> Observation:
        return self._run_command(action.command)

    async def run_ipython(self, action: IPythonRunCellAction) -> Observation:
        obs = self._run_command(
            ("cat > /tmp/opendevin_jupyter_temp.py <<'EOL'\n" f'{action.code}\n' 'EOL'),
        )

        # run the code
        obs = self._run_command('cat /tmp/opendevin_jupyter_temp.py | execute_cli')
        output = obs.content
        if 'pip install' in action.code:
            print(output)
            package_names = action.code.split(' ', 2)[-1]
            is_single_package = ' ' not in package_names

            if 'Successfully installed' in output:
                restart_kernel = 'import IPython\nIPython.Application.instance().kernel.do_shutdown(True)'
                if (
                    'Note: you may need to restart the kernel to use updated packages.'
                    in output
                ):
                    self._run_command(
                        (
                            "cat > /tmp/opendevin_jupyter_temp.py <<'EOL'\n"
                            f'{restart_kernel}\n'
                            'EOL'
                        )
                    )
                    obs = self._run_command(
                        'cat /tmp/opendevin_jupyter_temp.py | execute_cli'
                    )
                    output = '[Package installed successfully]'
                    if "{'status': 'ok', 'restart': True}" != obs.content.strip():
                        print(obs.content)
                        output += (
                            '\n[But failed to restart the kernel to load the package]'
                        )
                    else:
                        output += (
                            '\n[Kernel restarted successfully to load the package]'
                        )

                    # re-init the kernel after restart
                    if action.kernel_init_code:
                        obs = self._run_command(
                            (
                                f"cat > /tmp/opendevin_jupyter_init.py <<'EOL'\n"
                                f'{action.kernel_init_code}\n'
                                'EOL'
                            ),
                        )
                        obs = self._run_command(
                            'cat /tmp/opendevin_jupyter_init.py | execute_cli',
                        )
            elif (
                is_single_package
                and f'Requirement already satisfied: {package_names}' in output
            ):
                output = '[Package already installed]'
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

    def _run_command(self, command: str) -> Observation:
        try:
            exit_code, output = self.sandbox.execute(command)
            if 'pip install' in command:
                package_names = command.split(' ', 2)[-1]
                is_single_package = ' ' not in package_names
                print(output)
                if 'Successfully installed' in output:
                    output = '[Package installed successfully]'
                elif (
                    is_single_package
                    and f'Requirement already satisfied: {package_names}' in output
                ):
                    output = '[Package already installed]'
            return CmdOutputObservation(
                command_id=-1, content=str(output), command=command, exit_code=exit_code
            )
        except UnicodeDecodeError:
            return ErrorObservation('Command output could not be decoded as utf-8')
