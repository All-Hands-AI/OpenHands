import json
import os
from abc import ABC, abstractmethod
from typing import Any, Optional

from opendevin.core.config import config
from opendevin.core.exceptions import BrowserInitException
from opendevin.core.logger import opendevin_logger as logger
from opendevin.events import EventStream, EventStreamSubscriber
from opendevin.events.action import (
    Action,
    AgentRecallAction,
    BrowseInteractiveAction,
    BrowseURLAction,
    CmdRunAction,
    FileReadAction,
    FileWriteAction,
    IPythonRunCellAction,
)
from opendevin.events.event import Event
from opendevin.events.observation import (
    CmdOutputObservation,
    ErrorObservation,
    IPythonRunCellObservation,
    NullObservation,
    Observation,
)
from opendevin.events.serialization.action import ACTION_TYPE_TO_CLASS
from opendevin.runtime.browser.browser_env import BrowserEnv
from opendevin.runtime.plugins import PluginRequirement
from opendevin.runtime.plugins.mixin import PluginMixin
from opendevin.runtime.tools import RuntimeTool
from opendevin.runtime.utils.browse import browse
from opendevin.runtime.utils.files import read_file, write_file
from opendevin.storage import FileStore, InMemoryFileStore


async def run_command_decorator(run_command_fn):
    """
    Decorator to handle observation of pip install commands.
    """

    async def wrapper(self, action: CmdRunAction) -> CmdOutputObservation:
        obs = await run_command_fn(self, action)

        if 'pip install' in action.command:
            package_names = action.command.split(' ', 2)[-1]
            is_single_package = ' ' not in package_names
            print(obs.content)
            if 'Successfully installed' in obs.content:
                obs.content = '[Package installed successfully]'
            elif (
                is_single_package
                and f'Requirement already satisfied: {package_names}' in obs.content
            ):
                obs.content = '[Package already installed]'

        return obs

    return wrapper


class Runtime(ABC, PluginMixin):
    """
    The runtime is how the agent interacts with the external environment.
    This implements a bash sandbox, a browser, and filesystem interactions.

    sid is the session id, which is used to identify the current user session.
    """

    sid: str
    file_store: FileStore

    def __init__(self, event_stream: EventStream, sid: str = 'default'):
        self.sid = sid
        self.browser: BrowserEnv | None = None
        self.file_store = InMemoryFileStore()
        self.event_stream = event_stream
        self.event_stream.subscribe(EventStreamSubscriber.RUNTIME, self.on_event)
        self.init_env_vars()

    @property
    def cwd(self) -> str:
        """
        Get the current working directory.
        """
        obs: CmdOutputObservation = self.run_command('pwd')
        if obs.exit_code != 0:
            raise RuntimeError('Failed to get current working directory')
        return str(obs.content).strip()

    @property
    def env(self) -> dict[str, str]:
        return self.env_vars._env

    def close(self):
        if self.browser is not None:
            self.browser.close()

    def init_env_vars(self):
        self._env: dict[str, str] = {}
        for key in os.environ:
            if key.startswith('SANDBOX_ENV_'):
                sandbox_key = key.removeprefix('SANDBOX_ENV_')
                self._add_to_env(sandbox_key, os.environ[key])
        if config.enable_auto_lint:
            self._add_to_env('ENABLE_AUTO_LINT', 'true')

    def _add_to_env(self, key: str, value: str):
        self._env[key] = value
        # Note: json.dumps gives us nice escaping for free
        self.run_command(f'export {key}={json.dumps(value)}')

    def init_sandbox_plugins(self, plugins: list[PluginRequirement]) -> None:
        pass

    def init_runtime_tools(
        self,
        runtime_tools: list[RuntimeTool],
        runtime_tools_config: Optional[dict[RuntimeTool, Any]] = None,
        is_async: bool = True,
    ) -> None:
        # TODO: Combine runtime tools with sandbox plugins
        # once we put the browser into the sandbox

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

    async def on_event(self, event: Event) -> None:
        if isinstance(event, Action):
            observation = await self.run_action(event)
            observation._cause = event.id  # type: ignore[attr-defined]
            self.event_stream.add_event(observation, event.source)  # type: ignore[arg-type]

    async def run_action(self, action: Action) -> Observation:
        """
        Run an action and return the resulting observation.
        If the action is not runnable in any runtime, a NullObservation is returned.
        If the action is not supported by the current runtime, an ErrorObservation is returned.
        """
        if not action.runnable:
            return NullObservation('')
        action_type = action.action  # type: ignore[attr-defined]
        if action_type not in ACTION_TYPE_TO_CLASS:
            return ErrorObservation(f'Action {action_type} does not exist.')
        if not hasattr(self, action_type):
            return ErrorObservation(
                f'Action {action_type} is not supported in the current runtime.'
            )
        observation = await getattr(self, action_type)(action)
        observation._parent = action.id  # type: ignore[attr-defined]
        return observation

    @abstractmethod
    @run_command_decorator
    async def run_command(self, action: CmdRunAction) -> CmdOutputObservation:
        """
        Run a command in the runtime.
        """
        raise NotImplementedError('Subclass must implement this method')

    async def run_ipython(
        self, action: IPythonRunCellAction
    ) -> IPythonRunCellObservation:
        """Run an IPython cell in the runtime.

        This requires the runtime to have a kernel.
        """
        obs = self.run_command(
            ("cat > /tmp/opendevin_jupyter_temp.py <<'EOL'\n" f'{action.code}\n' 'EOL'),
        )

        # run the code
        obs = self.run_command('cat /tmp/opendevin_jupyter_temp.py | execute_cli')
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
                    self.run_command(
                        (
                            "cat > /tmp/opendevin_jupyter_temp.py <<'EOL'\n"
                            f'{restart_kernel}\n'
                            'EOL'
                        )
                    )
                    obs = self.run_command(
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
                        obs = self.run_command(
                            (
                                f"cat > /tmp/opendevin_jupyter_init.py <<'EOL'\n"
                                f'{action.kernel_init_code}\n'
                                'EOL'
                            ),
                        )
                        obs = self.run_command(
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
        return await read_file(action.path, self.cwd, action.start, action.end)

    async def write(self, action: FileWriteAction) -> Observation:
        # TODO: use self.file_store
        return await write_file(
            action.path, self.cwd, action.content, action.start, action.end
        )

    async def browse(self, action: BrowseURLAction) -> Observation:
        return await browse(action, self.browser)

    async def browse_interactive(self, action: BrowseInteractiveAction) -> Observation:
        return await browse(action, self.browser)

    async def recall(self, action: AgentRecallAction) -> Observation:
        # TODO: Maybe we should remove this from Runtime?
        # This may fits better in the "Agent" class itself
        return NullObservation('')

    @abstractmethod
    async def copy_to(self, host_src: str, sandbox_dest: str, recursive: bool = False):
        pass
