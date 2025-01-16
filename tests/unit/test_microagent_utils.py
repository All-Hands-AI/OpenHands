import os

from pytest import MonkeyPatch

import openhands.agenthub  # noqa: F401
from openhands.utils.microagent import MicroAgent

CONTENT = (
    '# dummy header\n' 'dummy content\n' '## dummy subheader\n' 'dummy subcontent\n'
)


def test_micro_agent_load(tmp_path, monkeypatch: MonkeyPatch):
    with open(os.path.join(tmp_path, 'dummy.md'), 'w') as f:
        f.write(
            (
                '---\n'
                'name: dummy\n'
                'agent: CodeActAgent\n'
                'require_env_var:\n'
                '  SANDBOX_OPENHANDS_TEST_ENV_VAR: "Set this environment variable for testing purposes"\n'
                '---\n' + CONTENT
            )
        )

    # Patch the required environment variable
    monkeypatch.setenv('SANDBOX_OPENHANDS_TEST_ENV_VAR', 'dummy_value')

    micro_agent = MicroAgent(os.path.join(tmp_path, 'dummy.md'))
    assert micro_agent is not None
    assert micro_agent.content == CONTENT.strip()
