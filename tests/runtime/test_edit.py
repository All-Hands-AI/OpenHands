"""Edit-related tests for the EventStreamRuntime."""

import os

from conftest import (
    _close_test_runtime,
    _load_runtime,
)

from openhands.core.logger import openhands_logger as logger
from openhands.events.action import FileEditAction, FileReadAction
from openhands.events.observation import FileEditObservation

# ============================================================================================================================
# Bash-specific tests
# ============================================================================================================================

ORGINAL = """from flask import Flask
app = Flask(__name__)

@app.route('/')
def index():
    numbers = list(range(1, 11))
    return str(numbers)

if __name__ == '__main__':
    app.run(port=5000)
"""


def test_edit_from_scratch(temp_dir, box_class, run_as_openhands):
    runtime = _load_runtime(temp_dir, box_class, run_as_openhands)
    try:
        action = FileEditAction(
            content=ORGINAL,
            path=os.path.join('/workspace', 'app.py'),
        )
        logger.info(action, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

        assert isinstance(
            obs, FileEditObservation
        ), 'The observation should be a FileEditObservation.'

        action = FileReadAction(
            path=os.path.join('/workspace', 'app.py'),
        )
        obs = runtime.run_action(action)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert obs.content.strip() == ORGINAL.strip()

    finally:
        _close_test_runtime(runtime)


EDIT = """# above stays the same
@app.route('/')
def index():
    numbers = list(range(1, 11))
    return '<table>' + ''.join([f'<tr><td>{i}</td></tr>' for i in numbers]) + '</table>'
# below stays the same
"""


def test_edit(temp_dir, box_class, run_as_openhands):
    runtime = _load_runtime(temp_dir, box_class, run_as_openhands)
    try:
        action = FileEditAction(
            content=ORGINAL,
            path=os.path.join('/workspace', 'app.py'),
        )
        logger.info(action, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

        assert isinstance(
            obs, FileEditObservation
        ), 'The observation should be a FileEditObservation.'

        action = FileReadAction(
            path=os.path.join('/workspace', 'app.py'),
        )
        obs = runtime.run_action(action)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert obs.content.strip() == ORGINAL.strip()

        action = FileEditAction(
            content=EDIT,
            path=os.path.join('/workspace', 'app.py'),
        )
        obs = runtime.run_action(action)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert (
            obs.content.strip()
            == (
                '--- /workspace/app.py\n'
                '+++ /workspace/app.py\n'
                '@@ -4,7 +4,7 @@\n'
                " @app.route('/')\n"
                ' def index():\n'
                '     numbers = list(range(1, 11))\n'
                '-    return str(numbers)\n'
                "+    return '<table>' + ''.join([f'<tr><td>{i}</td></tr>' for i in numbers]) + '</table>'\n"
                '\n'
                " if __name__ == '__main__':\n"
                '     app.run(port=5000)\n'
            ).strip()
        )
    finally:
        _close_test_runtime(runtime)
