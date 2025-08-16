from pathlib import Path

import pytest

from openhands.events.action.files import FileEditAction
from openhands.events.event import FileEditSource
from openhands.runtime.action_execution_server import ActionExecutor
from openhands.runtime.plugins import AgentSkillsRequirement, JupyterRequirement


@pytest.mark.asyncio
async def test_runtime_routes_replace_to_gemini_editor(tmp_path):
    # Setup a minimal runtime with a temp workspace
    work_dir = str(tmp_path)
    plugins = []
    executor = ActionExecutor(
        plugins_to_load=plugins,
        work_dir=work_dir,
        # Use root to avoid useradd in test container environments
        username='root',
        user_id=0,
        enable_browser=False,
        browsergym_eval_env=None,
    )
    await executor.ainit()

    # Create a test file
    p = Path(work_dir) / 'a.txt'
    p.write_text('hello\nworld\n')

    action = FileEditAction(
        path=str(p),
        command='replace',
        impl_source=FileEditSource.OH_ACI,
        old_str='world',
        new_str='there',
    )

    obs = await executor.edit(action)
    assert obs.error is None
    assert 'has been edited' in obs.content or 'Edited' in obs.content
    # diff should reflect actual contents
    assert '-world' in obs.diff or '+there' in obs.diff
