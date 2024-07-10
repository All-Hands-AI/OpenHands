import argparse
import asyncio

import pexpect
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from uvicorn import run

from opendevin.core.logger import opendevin_logger as logger
from opendevin.events.action import (
    Action,
    CmdRunAction,
    IPythonRunCellAction,
)
from opendevin.events.observation import (
    CmdOutputObservation,
    Observation,
)
from opendevin.events.serialization import event_from_dict, event_to_dict
from opendevin.runtime.plugins import (
    ALL_PLUGINS,
    JupyterPlugin,
    Plugin,
)

app = FastAPI()


class ActionRequest(BaseModel):
    action: dict


class RuntimeClient:
    """RuntimeClient is running inside docker sandbox.
    It is responsible for executing actions received from OpenDevin backend and producing observations.
    """

    def __init__(self, plugins_to_load: list[Plugin]) -> None:
        self._init_bash_shell()
        self.lock = asyncio.Lock()
        self.plugins: dict[str, Plugin] = {}

        for plugin in plugins_to_load:
            plugin.initialize()
            self.plugins[plugin.name] = plugin
            logger.info(f'Initializing plugin: {plugin.name}')

    def _init_bash_shell(self) -> None:
        self.shell = pexpect.spawn('/bin/bash', encoding='utf-8', echo=False)
        self.shell.expect(r'[$#] ')

    def _execute_bash(self, command):
        logger.info(f'Received command: {command}')
        self.shell.sendline(command)
        self.shell.expect(r'[$#] ')
        output = self.shell.before + '# '

        self.shell.sendline('echo $?')
        self.shell.expect(r'[$#] ')
        exit_code = int(self.shell.before.split('\r\n')[0].strip())
        return output, exit_code

    async def run_action(self, action) -> Observation:
        action_type = action.action
        observation = await getattr(self, action_type)(action)
        observation._parent = action.id
        return observation

    async def run(self, action: CmdRunAction) -> CmdOutputObservation:
        try:
            output, exit_code = self._execute_bash(action.command)
            return CmdOutputObservation(
                command_id=-1,
                content=str(output),
                command=action.command,
                exit_code=exit_code,
            )
        except UnicodeDecodeError:
            raise RuntimeError('Command output could not be decoded as utf-8')

    async def run_ipython(self, action: IPythonRunCellAction) -> Observation:
        if 'jupyter' in self.plugins:
            _jupyter_plugin: JupyterPlugin = self.plugins['jupyter']  # type: ignore
            return await _jupyter_plugin.run(action)
        else:
            raise RuntimeError(
                'JupyterRequirement not found. Unable to run IPython action.'
            )

    def close(self):
        self.shell.close()


# def test_run_commond():
#     client = RuntimeClient()
#     command = CmdRunAction(command='ls -l')
#     obs = client.run_action(command)
#     print(obs)

# def test_shell(message):
#     shell = pexpect.spawn('/bin/bash', encoding='utf-8')
#     shell.expect(r'[$#] ')
#     print(f'Received command: {message}')
#     shell.sendline(message)
#     shell.expect(r'[$#] ')
#     output = shell.before.strip().split('\r\n', 1)[1].strip()
#     print(f'Output: {output}')
#     shell.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('port', type=int, help='Port to listen on')
    parser.add_argument('--plugins', type=str, help='Plugins to initialize', nargs='+')
    # example: python client.py 8000 --plugins JupyterRequirement
    args = parser.parse_args()

    plugins_to_load: list[Plugin] = []
    if args.plugins:
        for plugin in args.plugins:
            if plugin not in ALL_PLUGINS:
                raise ValueError(f'Plugin {plugin} not found')
            plugins_to_load.append(ALL_PLUGINS[plugin]())  # type: ignore

    client = RuntimeClient(plugins_to_load)

    @app.middleware('http')
    async def one_request_at_a_time(request: Request, call_next):
        async with client.lock:
            response = await call_next(request)
        return response

    @app.post('/execute_action')
    async def execute_action(action_request: ActionRequest):
        try:
            action = event_from_dict(action_request.action)
            if not isinstance(action, Action):
                raise HTTPException(status_code=400, detail='Invalid action type')
            observation = await client.run_action(action)
            return event_to_dict(observation)
        except Exception as e:
            logger.error(f'Error processing command: {str(e)}')
            raise HTTPException(status_code=500, detail=str(e))

    @app.get('/alive')
    async def alive():
        return {'status': 'ok'}

    logger.info(f'Starting action execution API on port {args.port}')
    print(f'Starting action execution API on port {args.port}')
    run(app, host='0.0.0.0', port=args.port)
