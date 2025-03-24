"""Browsing-related tests for the DockerRuntime, which connects to the ActionExecutor running in the sandbox."""

import os

from conftest import _close_test_runtime, _load_runtime

from openhands.core.logger import openhands_logger as logger
from openhands.events.action import (
    BrowseInteractiveAction,
    BrowseURLAction,
    CmdRunAction,
)
from openhands.events.observation import (
    BrowserOutputObservation,
    CmdOutputObservation,
)

# ============================================================================================================================
# Browsing tests, without evaluation (poetry install --without evaluation)
# For eval environments, tests need to run with poetry install
# ============================================================================================================================


def test_simple_browse(temp_dir, runtime_cls, run_as_openhands):
    runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands)

    # Test browse
    action_cmd = CmdRunAction(command='python3 -m http.server 8000 > server.log 2>&1 &')
    logger.info(action_cmd, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action_cmd)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})

    assert isinstance(obs, CmdOutputObservation)
    assert obs.exit_code == 0
    assert '[1]' in obs.content

    action_cmd = CmdRunAction(command='sleep 3 && cat server.log')
    logger.info(action_cmd, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action_cmd)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert obs.exit_code == 0

    action_browse = BrowseURLAction(url='http://localhost:8000')
    logger.info(action_browse, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action_browse)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})

    assert isinstance(obs, BrowserOutputObservation)
    assert 'http://localhost:8000' in obs.url
    assert not obs.error
    assert obs.open_pages_urls == ['http://localhost:8000/']
    assert obs.active_page_index == 0
    assert obs.last_browser_action == 'goto("http://localhost:8000")'
    assert obs.last_browser_action_error == ''
    assert 'Directory listing for /' in obs.content
    assert 'server.log' in obs.content

    # clean up
    action = CmdRunAction(command='rm -rf server.log')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert obs.exit_code == 0

    _close_test_runtime(runtime)


def test_read_pdf_browse(temp_dir, runtime_cls, run_as_openhands):
    runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    try:
        # Create a PDF file using reportlab in the host environment
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas

        pdf_path = os.path.join(temp_dir, 'test_document.pdf')
        pdf_content = 'This is test content for PDF reading test'

        c = canvas.Canvas(pdf_path, pagesize=letter)
        # Add more content to make the PDF more robust
        c.drawString(100, 750, pdf_content)
        c.drawString(100, 700, 'Additional line for PDF structure')
        c.drawString(100, 650, 'Third line to ensure valid PDF')
        # Explicitly set PDF version and ensure proper structure
        c.setPageCompression(0)  # Disable compression for simpler structure
        c.save()

        # Copy the PDF to the sandbox
        sandbox_dir = config.workspace_mount_path_in_sandbox
        runtime.copy_to(pdf_path, sandbox_dir)

        # Start HTTP server
        action_cmd = CmdRunAction(command='ls -alh')
        logger.info(action_cmd, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_cmd)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert isinstance(obs, CmdOutputObservation)
        assert obs.exit_code == 0
        assert 'test_document.pdf' in obs.content

        # Get server url
        action_cmd = CmdRunAction(command='cat /openhands/oh-server-url')
        logger.info(action_cmd, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_cmd)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert obs.exit_code == 0
        server_url = obs.content.strip()

        # Browse to the PDF file
        pdf_url = f'{server_url}/view?path=/workspace/test_document.pdf'
        action_browse = BrowseInteractiveAction(browser_actions=f'goto("{pdf_url}")')
        logger.info(action_browse, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_browse)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

        # Verify the browser observation
        assert isinstance(obs, BrowserOutputObservation)
        observation_text = str(obs)
        assert '[Action executed successfully.]' in observation_text
        assert 'Canvas' in observation_text

    finally:
        _close_test_runtime(runtime)
