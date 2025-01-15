import asyncio
import time
from openhands.core.logger import openhands_logger as logger
from openhands.events.action.commands import CmdRunAction, IPythonRunCellAction
from openhands.events.observation.commands import CmdOutputObservation
from openhands.events.observation.error import ErrorObservation
from openhands.runtime.browser.browser_env import BrowserEnv
from openhands.runtime.plugins.jupyter import JupyterPlugin
from openhands.runtime.plugins.requirement import Plugin
from openhands.runtime.utils.bash import BashSession
from openhands.runtime.utils.runtime_init import init_user_and_working_directory
from openhands.utils.async_utils import call_sync_from_async, wait_all


ROOT_GID = 0
INIT_COMMANDS = [
    'git config --global user.name "openhands" && git config --global user.email "openhands@all-hands.dev" && alias git="git --no-pager"',
]


class RuntimeExecutor:
    """RuntimeExecutor for running inside docker sandbox.
    It provides a minimal base class that handles initialization of the executor, and provides a run method to execute bash commands.
    """

    def __init__(
        self,
        plugins_to_load: list[Plugin],
        work_dir: str,
        username: str,
        user_id: int,
        browsergym_eval_env: str | None,
    ) -> None:
        self.plugins_to_load = plugins_to_load
        self._initial_cwd = work_dir
        self.username = username
        self.user_id = user_id
        _updated_user_id = init_user_and_working_directory(
            username=username, user_id=self.user_id, initial_cwd=work_dir
        )
        if _updated_user_id is not None:
            self.user_id = _updated_user_id

        self.bash_session: BashSession | None = None
        self.lock = asyncio.Lock()
        self.plugins: dict[str, Plugin] = {}
        self.browser = BrowserEnv(browsergym_eval_env)
        self.start_time = time.time()
        self.last_execution_time = self.start_time
        self._initialized = False

    @property
    def initial_cwd(self):
        return self._initial_cwd

    async def ainit(self):
        # bash needs to be initialized first
        self.bash_session = BashSession(
            work_dir=self._initial_cwd,
            username=self.username,
        )
        self.bash_session.initialize()
        await wait_all(
            (self._init_plugin(plugin) for plugin in self.plugins_to_load),
            timeout=30,
        )

        # This is a temporary workaround
        # TODO: refactor AgentSkills to be part of JupyterPlugin
        # AFTER ServerRuntime is deprecated
        if 'agent_skills' in self.plugins and 'jupyter' in self.plugins:
            obs = await self.run_ipython(
                IPythonRunCellAction(
                    code='from openhands.runtime.plugins.agent_skills.agentskills import *\n'
                )
            )
            logger.debug(f'AgentSkills initialized: {obs}')

        await self._init_bash_commands()
        logger.debug('Runtime client initialized.')

        self._initialized = True

    @property
    def initialized(self) -> bool:
        return self._initialized

    async def _init_plugin(self, plugin: Plugin):
        assert self.bash_session is not None
        await plugin.initialize(self.username)
        self.plugins[plugin.name] = plugin
        logger.debug(f'Initializing plugin: {plugin.name}')

        if isinstance(plugin, JupyterPlugin):
            await self.run_ipython(
                IPythonRunCellAction(
                    code=f'import os; os.chdir("{self.bash_session.cwd}")'
                )
            )

    async def _init_bash_commands(self):
        logger.debug(f'Initializing by running {len(INIT_COMMANDS)} bash commands...')
        for command in INIT_COMMANDS:
            action = CmdRunAction(command=command)
            action.timeout = 300
            logger.debug(f'Executing init command: {command}')
            obs = await self.run(action)
            assert isinstance(obs, CmdOutputObservation)
            logger.debug(
                f'Init command outputs (exit code: {obs.exit_code}): {obs.content}'
            )
            assert obs.exit_code == 0

        logger.debug('Bash init commands completed')

    async def run(
        self, action: CmdRunAction
    ) -> CmdOutputObservation | ErrorObservation:
        assert self.bash_session is not None
        obs = await call_sync_from_async(self.bash_session.execute, action)
        return obs

    def close(self):
        if self.bash_session is not None:
            self.bash_session.close()
        self.browser.close()
