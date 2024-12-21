import os
import tempfile

import pytest

from openhands.events.action import CmdRunAction
from openhands.events.event import EventSource
from openhands.runtime.utils.bash import BashSession


def test_interactive_command():
    # Create a temporary script that requires input
    script_content = '''#!/bin/bash
echo "Enter your name:"
read name
echo "Hello, $name!"
'''
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
        f.write(script_content)
        script_path = f.name
    os.chmod(script_path, 0o755)

    try:
        # Initialize bash session
        session = BashSession(os.path.dirname(script_path), "root")

        # Run the script - it should wait for input
        action = CmdRunAction(
            command=script_path,
            blocking=False,  # Non-blocking to handle interactive input
            timeout=5,
            source=EventSource.AGENT,
        )
        result = session.run(action)
        assert result.exit_code == -1  # Indicates waiting for input
        assert "Enter your name:" in result.content

        # Send input
        action = CmdRunAction(
            command="",  # Empty command to continue previous execution
            input_text="Alice",
            blocking=False,
            timeout=5,
            source=EventSource.AGENT,
        )
        result = session.run(action)
        assert result.exit_code == 0
        assert "Hello, Alice!" in result.content

    finally:
        # Clean up
        os.unlink(script_path)
        session.close()