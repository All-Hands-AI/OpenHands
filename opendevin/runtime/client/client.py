import argparse
import asyncio
import os
import shutil

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
    IPythonRunCellObservation,
    Observation,
)
from opendevin.events.serialization import event_from_dict, event_to_dict
from opendevin.runtime.plugins import (
    PluginRequirement,
)

app = FastAPI()


class ActionRequest(BaseModel):
    action: dict


class RuntimeClient:
    def __init__(self) -> None:
        self.init_shell()
        self.lock = asyncio.Lock()

    def init_shell(self) -> None:
        self.shell = pexpect.spawn('/bin/bash', encoding='utf-8', echo=False)
        self.shell.expect(r'[$#] ')

    def run_action(self, action) -> Observation:
        action_type = action.action
        observation = getattr(self, action_type)(action)
        observation._parent = action.id
        return observation

    def run(self, action: CmdRunAction) -> CmdOutputObservation:
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

    def _execute_bash(self, command):
        logger.info(f'Received command: {command}')
        self.shell.sendline(command)
        self.shell.expect(r'[$#] ')
        output = self.shell.before + '# '

        self.shell.sendline('echo $?')
        self.shell.expect(r'[$#] ')
        exit_code = int(self.shell.before.split('\r\n')[0].strip())
        return output, exit_code

    def run_ipython(self, action: IPythonRunCellAction) -> Observation:
        obs = self.run(
            CmdRunAction(
                command="cat > /tmp/opendevin_jupyter_temp.py <<'EOL'\n"
                f'{action.code}\n'
                'EOL'
            ),
        )
        # run the code
        obs = self.run(
            CmdRunAction(command='cat /tmp/opendevin_jupyter_temp.py | execute_cli')
        )
        output = obs.content
        if 'pip install' in action.code:
            package_names = action.code.split(' ', 2)[-1]
            is_single_package = ' ' not in package_names

            if 'Successfully installed' in output:
                restart_kernel = 'import IPython\nIPython.Application.instance().kernel.do_shutdown(True)'
                if (
                    'Note: you may need to restart the kernel to use updated packages.'
                    in output
                ):
                    self.run(
                        CmdRunAction(
                            command="cat > /tmp/opendevin_jupyter_temp.py <<'EOL'\n"
                            f'{restart_kernel}\n'
                            'EOL'
                        )
                    )
                    obs = self.run(
                        CmdRunAction(
                            command='cat /tmp/opendevin_jupyter_temp.py | execute_cli'
                        )
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
                        obs = self.run(
                            CmdRunAction(
                                command=f"cat > /tmp/opendevin_jupyter_init.py <<'EOL'\n"
                                f'{action.kernel_init_code}\n'
                                'EOL'
                            ),
                        )
                        obs = self.run(
                            CmdRunAction(
                                command='cat /tmp/opendevin_jupyter_init.py | execute_cli'
                            ),
                        )
            elif (
                is_single_package
                and f'Requirement already satisfied: {package_names}' in output
            ):
                output = '[Package already installed]'
        return IPythonRunCellObservation(content=output, code=action.code)

    def close(self):
        self.shell.close()

    ############################################################################
    # Initialization work inside sandbox image
    ############################################################################

    # init_runtime_tools do in EventStreamRuntime

    def init_sandbox_plugins(self, requirements: list[PluginRequirement]) -> None:
        # TODO:: test after settle donw the way to move code into sandbox
        for requirement in requirements:
            self._source_bashrc()

            shutil.copytree(requirement.host_src, requirement.sandbox_dest)

            # Execute the bash script
            abs_path_to_bash_script = os.path.join(
                requirement.sandbox_dest, requirement.bash_script_path
            )

            print(
                f'Initializing plugin [{requirement.name}] by executing [{abs_path_to_bash_script}] in the sandbox.'
            )
            res = self.run(CmdRunAction(command=abs_path_to_bash_script))
            if res.exit_code != 0:
                raise RuntimeError(
                    f'Failed to initialize plugin {requirement.name} with exit code {res.exit_code} and output: {res.content}'
                )
            print(f'Plugin {requirement.name} initialized successfully.')
        if len(requirements) > 0:
            self._source_bashrc()

    def _source_bashrc(self):
        res = self.run(
            CmdRunAction(command='source /opendevin/bash.bashrc && source ~/.bashrc')
        )
        if res.exit_code != 0:
            raise RuntimeError(
                f'Failed to source /opendevin/bash.bashrc and ~/.bashrc with exit code {res.exit_code} and output: {res.content}'
            )
        print('Sourced /opendevin/bash.bashrc and ~/.bashrc successfully')


client = RuntimeClient()


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
        observation = client.run_action(action)
        return event_to_dict(observation)
    except Exception as e:
        logger.error(f'Error processing command: {str(e)}')
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/alive')
async def alive():
    return {'status': 'ok'}


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
    args = parser.parse_args()
    logger.info(f'Starting action execution API on port {args.port}')
    print(f'Starting action execution API on port {args.port}')
    run(app, host='0.0.0.0', port=args.port)
