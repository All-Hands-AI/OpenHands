from typing import Callable

import tenacity

from openhands.a2a.A2AManager import A2AManager
from openhands.core.config import AppConfig
from openhands.core.logger import openhands_logger as logger
from openhands.events import EventStream
from openhands.runtime.impl.action_execution.action_execution_client import (
    ActionExecutionClient,
)
from openhands.runtime.plugins import PluginRequirement
from openhands.utils.http_session import HttpSession
from openhands.utils.tenacity_stop import stop_if_should_exit


class PyodideRuntime(ActionExecutionClient):
    """The PyodideRuntime class is an PyodideRuntime that utilizes Pyodide MCP as a runtime environment to execute bash and edit files."""

    def __init__(
        self,
        config: AppConfig,
        event_stream: EventStream,
        sid: str = 'default',
        plugins: list[PluginRequirement] | None = None,
        env_vars: dict[str, str] | None = None,
        status_callback: Callable | None = None,
        attach_to_existing: bool = False,
        headless_mode: bool = True,
        a2a_manager: A2AManager | None = None,
        mnemonic: str | None = None,
    ):
        super().__init__(
            config,
            event_stream,
            sid,
            plugins,
            env_vars,
            status_callback,
            attach_to_existing,
            headless_mode,
            a2a_manager=a2a_manager,
            mnemonic=mnemonic,
        )
        self.config = config
        self.status_callback = status_callback
        self.sid = sid
        user_id = self.user_id if self.user_id else self.event_stream.user_id
        self.session = HttpSession(
            headers={
                'session_id': self.sid,
                'user_id': user_id if user_id else '',
            }
        )

    def _get_action_execution_server_host(self):
        return self.api_url

    async def connect(self):
        pyodide_mcp_config = self.config.dict_mcp_config['pyodide']
        if pyodide_mcp_config is None:
            raise ValueError('Pyodide MCP config not found')

        if not hasattr(pyodide_mcp_config, 'url') or not pyodide_mcp_config.url:
            raise ValueError('Pyodide MCP URL not configured')

        self.api_url = pyodide_mcp_config.url.replace('/sse', '')
        logger.info(f'Container started. Server url: {self.api_url}')

        logger.info('Waiting for client to become ready...')
        self.send_status_message('STATUS$WAITING_FOR_CLIENT')
        # no need to check if alive. If the service is dead -> others won't be able to use.
        # self._wait_until_alive()

        # self._send_action_server_request(
        #     'POST',
        #     f'{self._get_action_execution_server_host()}/connect',
        # )

        logger.info('Pyodide initialized')
        self.send_status_message(' ')

    @tenacity.retry(
        stop=tenacity.stop_after_delay(120) | stop_if_should_exit(),
        wait=tenacity.wait_fixed(1),
        reraise=(ConnectionRefusedError,),
    )
    def _wait_until_alive(self):
        super().check_if_alive()

    def close(self):
        super().close()

    @property
    def vscode_url(self) -> str | None:
        return None
