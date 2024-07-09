import asyncio
import os
import websockets
import pexpect
import json
import shutil
from typing import Any
from websockets.exceptions import ConnectionClosed
from opendevin.events.serialization import event_to_dict, event_from_dict
from opendevin.events.observation import Observation
from opendevin.runtime.plugins import PluginRequirement
from opendevin.events.action import (
    Action,
    CmdRunAction,
    IPythonRunCellAction,
)
from opendevin.events.observation import (
    CmdOutputObservation,
    ErrorObservation,
    Observation,
    IPythonRunCellObservation
)
from opendevin.runtime.plugins import (
    AgentSkillsRequirement,
    JupyterRequirement,
    PluginRequirement,
)

class RuntimeClient():
    # This runtime will listen to the websocket
    # When receive an event, it will run the action and send the observation back to the websocket

    def __init__(self) -> None:
        self.init_shell()
        # TODO: code will block at init_websocket, maybe we can open a subprocess to run websocket forever
        # In case we need to run other code after init_websocket
        self.init_websocket()

    def init_websocket(self) -> None:
        server = websockets.serve(self.listen, "0.0.0.0", 8080)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(server)
        loop.run_forever()
    
    def init_shell(self) -> None:
        # TODO: we need to figure a way to support different users. Maybe the runtime cli should be run as root
        self.shell = pexpect.spawn('/bin/bash', encoding='utf-8')
        self.shell.expect(r'[$#] ')

    async def listen(self, websocket):
        try:
            async for message in websocket:
                event_str = json.loads(message)
                event = event_from_dict(event_str)
                if isinstance(event, Action):
                    observation = self.run_action(event)
                    await websocket.send(json.dumps(event_to_dict(observation)))
        except ConnectionClosed:
            print("Connection closed")
    
    def run_action(self, action) -> Observation:
        # Should only receive Action CmdRunAction and IPythonRunCellAction
        action_type = action.action  # type: ignore[attr-defined]
        observation = getattr(self, action_type)(action)
        # TODO: see comments in https://github.com/OpenDevin/OpenDevin/pull/2603#discussion_r1668994137
        observation._parent = action.id  # type: ignore[attr-defined]
        return observation
    
    def run(self, action: CmdRunAction) -> Observation:
        return self._run_command(action.command)
    
    def _run_command(self, command: str) -> Observation:
        try:
            output, exit_code = self.execute(command)
            return CmdOutputObservation(
                command_id=-1, content=str(output), command=command, exit_code=exit_code
            )
        except UnicodeDecodeError:
            return ErrorObservation('Command output could not be decoded as utf-8')
           
    def execute(self, command):
        print(f"Received command: {command}")
        self.shell.sendline(command)
        self.shell.expect(r'[$#] ')
        output = self.shell.before.strip().split('\r\n', 1)[1].strip()
        exit_code = output[-1].strip()
        return output, exit_code

    def run_ipython(self, action: IPythonRunCellAction) -> Observation:
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
            output, exit_code = self.execute(abs_path_to_bash_script)
            if exit_code != 0:
                raise RuntimeError(
                    f'Failed to initialize plugin {requirement.name} with exit code {exit_code} and output: {output}'
                )
            print(f'Plugin {requirement.name} initialized successfully.')
        if len(requirements) > 0:
            self._source_bashrc()
    
    def _source_bashrc(self):
        output, exit_code = self.execute(
            'source /opendevin/bash.bashrc && source ~/.bashrc'
        )
        if exit_code != 0:
            raise RuntimeError(
                f'Failed to source /opendevin/bash.bashrc and ~/.bashrc with exit code {exit_code} and output: {output}'
            )
        print('Sourced /opendevin/bash.bashrc and ~/.bashrc successfully')


def test_run_commond():
    client = RuntimeClient()
    command = CmdRunAction(command="ls -l")
    obs = client.run_action(command)
    print(obs)


def test_shell(message):
    shell = pexpect.spawn('/bin/bash', encoding='utf-8')
    shell.expect(r'[$#] ')
    print(f"Received command: {message}")
    shell.sendline(message)
    shell.expect(r'[$#] ')
    output = shell.before.strip().split('\r\n', 1)[1].strip()
    shell.close()

if __name__ == "__main__":
    # print(test_shell("ls -l"))
    client = RuntimeClient()
    # test_run_commond()
    # client.init_sandbox_plugins([AgentSkillsRequirement,JupyterRequirement])

    