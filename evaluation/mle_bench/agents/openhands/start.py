"""
Main entrypoint for the OpenHands agent.
"""

import argparse
import asyncio
import json
import os
from pathlib import Path
from typing import Callable, Iterable

from openhands.controller.state.state import State
from openhands.core.config import load_app_config
from openhands.core.main import create_runtime, run_controller
from openhands.events import Event, EventStreamSubscriber
from openhands.events.action import (
    Action,
    CmdRunAction,
    IPythonRunCellAction,
    MessageAction,
)
from openhands.events.observation import (
    CmdOutputObservation,
    IPythonRunCellObservation,
)

# pylint: disable=unspecified-encoding

parser = argparse.ArgumentParser()
parser.add_argument('--max_time_in_hours', type=float, required=True)
args, other_args = parser.parse_known_args()

global_events = []
global_events_lock = asyncio.Lock()

CODE_DIR = Path(os.getenv('CODE_DIR'))  # type: ignore
MAX_TIME_IN_SECONDS = args.max_time_in_hours * 60 * 60


def fake_user_response_fn(
    _state: State,
    _encapsulate_solution: bool = False,
    _try_parse: Callable[[Action], str] | None = None,
) -> str:
    return 'Please continue working on the approach you think is most promising. You should complete the task without any human input.'


async def on_event(event: Event):
    """Used to stream the agent's Jupyter notebook and Python code to the code directory."""

    async with global_events_lock:
        global_events.append(event)
        notebook = get_notebook(global_events)
        python = get_python(global_events)

        with open(CODE_DIR / 'solution.ipynb', 'w') as file:
            json.dump(notebook, file)

        with open(CODE_DIR / 'solution.py', 'w') as file:
            file.write(python)


async def run(instructions: str) -> State:
    config = load_app_config()

    runtime = create_runtime(config)
    runtime.event_stream.subscribe(EventStreamSubscriber.TEST, on_event, 'mle-bench')
    await runtime.connect()

    state: State | None = await asyncio.wait_for(
        run_controller(
            config=config,
            initial_user_action=MessageAction(content=instructions),
            runtime=runtime,
            exit_on_message=False,
            fake_user_response_fn=fake_user_response_fn,
        ),
        timeout=MAX_TIME_IN_SECONDS,
    )

    assert state, 'Controller produced no final state.'
    return state


def get_python(events: Iterable[Event]) -> str:
    code = '# %%\n\n'
    sep = '\n\n# %%\n\n'

    for event in events:
        if isinstance(event, IPythonRunCellAction):
            code += event.code + sep
        elif isinstance(event, CmdRunAction):
            code += f'!{event.command}' + sep

    return code


def get_notebook(events: Iterable[Event]) -> dict:
    cells = []

    for event in events:
        if event.source != 'agent':
            continue

        if isinstance(event, IPythonRunCellAction):
            cells.append(
                {
                    'cell_type': 'markdown',
                    'metadata': {},
                    'source': [event.thought],
                }
            )
            cells.append(
                {
                    'cell_type': 'code',
                    'metadata': {},
                    'source': event.code.split('\n'),
                    'outputs': [],
                    'execution_count': None,
                }
            )
        elif isinstance(event, IPythonRunCellObservation):
            assert cells
            assert cells[-1]['cell_type'] == 'code'

            cells[-1]['outputs'].append(
                {
                    'name': 'stdout',
                    'output_type': 'stream',
                    'text': event.content.split('\n'),
                }
            )
        elif isinstance(event, CmdRunAction):
            cells.append(
                {
                    'cell_type': 'code',
                    'metadata': {},
                    'source': [f'!{event.command}'],
                    'outputs': [],
                    'execution_count': None,
                }
            )
        elif isinstance(event, CmdOutputObservation):
            assert cells
            assert cells[-1]['cell_type'] == 'code'

            cells[-1]['outputs'].append(
                {
                    'name': 'stdout',
                    'output_type': 'stream',
                    'text': event.content.split('\n'),
                }
            )

    notebook = {
        'cells': cells,
        'metadata': {
            'kernelspec': {
                'display_name': 'Python 3',
                'language': 'python',
                'name': 'python3',
            },
            'language_info': {
                'codemirror_mode': {'name': 'ipython', 'version': 3},
                'file_extension': '.py',
                'mimetype': 'text/x-python',
                'name': 'python',
                'nbconvert_exporter': 'python',
                'pygments_lexer': 'ipython3',
                'version': '3.11.0',
            },
        },
        'nbformat': 4,
        'nbformat_minor': 4,
    }

    return notebook


if __name__ == '__main__':
    with open('/home/full_instructions.txt', 'r') as file:
        instructions = file.read()

    asyncio.run(run(instructions))
