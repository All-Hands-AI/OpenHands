"""Browsing-related tests for the DockerRuntime, which connects to the ActionExecutor running in the sandbox."""

import os

import pytest
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


@pytest.mark.skipif(
    os.environ.get('TEST_RUNTIME') == 'cli',
    reason='CLIRuntime does not support browsing actions',
)
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

    action_browse = BrowseURLAction(url='http://localhost:8000', return_axtree=False)
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


@pytest.mark.skipif(
    os.environ.get('TEST_RUNTIME') == 'cli',
    reason='CLIRuntime does not support browsing actions',
)
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
        action_cmd = CmdRunAction(command='cat /tmp/oh-server-url')
        logger.info(action_cmd, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_cmd)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert obs.exit_code == 0
        server_url = obs.content.strip()

        # Browse to the PDF file
        pdf_url = f'{server_url}/view?path=/workspace/test_document.pdf'
        action_browse = BrowseInteractiveAction(
            browser_actions=f'goto("{pdf_url}")', return_axtree=False
        )
        logger.info(action_browse, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_browse)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

        # Verify the browser observation
        assert isinstance(obs, BrowserOutputObservation)
        observation_text = str(obs)
        assert '[Action executed successfully.]' in observation_text
        assert 'Canvas' in observation_text
        assert (
            'Screenshot saved to: /workspace/.browser_screenshots/screenshot_'
            in observation_text
        )

        # Check the /workspace/.browser_screenshots folder
        action_cmd = CmdRunAction(command='ls /workspace/.browser_screenshots')
        logger.info(action_cmd, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_cmd)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert isinstance(obs, CmdOutputObservation)
        assert obs.exit_code == 0
        assert 'screenshot_' in obs.content
        assert '.png' in obs.content
    finally:
        _close_test_runtime(runtime)


@pytest.mark.skipif(
    os.environ.get('TEST_RUNTIME') == 'cli',
    reason='CLIRuntime does not support browsing actions',
)
def test_read_png_browse(temp_dir, runtime_cls, run_as_openhands):
    runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    try:
        # Create a PNG file using PIL in the host environment
        from PIL import Image, ImageDraw

        png_path = os.path.join(temp_dir, 'test_image.png')
        # Create a simple image with text
        img = Image.new('RGB', (400, 200), color=(255, 255, 255))
        d = ImageDraw.Draw(img)
        text = 'This is a test PNG image'
        d.text((20, 80), text, fill=(0, 0, 0))
        img.save(png_path)

        # Copy the PNG to the sandbox
        sandbox_dir = config.workspace_mount_path_in_sandbox
        runtime.copy_to(png_path, sandbox_dir)

        # Verify the file exists in the sandbox
        action_cmd = CmdRunAction(command='ls -alh')
        logger.info(action_cmd, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_cmd)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert isinstance(obs, CmdOutputObservation)
        assert obs.exit_code == 0
        assert 'test_image.png' in obs.content

        # Get server url
        action_cmd = CmdRunAction(command='cat /tmp/oh-server-url')
        logger.info(action_cmd, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_cmd)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert obs.exit_code == 0
        server_url = obs.content.strip()

        # Browse to the PNG file
        png_url = f'{server_url}/view?path=/workspace/test_image.png'
        action_browse = BrowseInteractiveAction(
            browser_actions=f'goto("{png_url}")', return_axtree=False
        )
        logger.info(action_browse, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_browse)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

        # Verify the browser observation
        assert isinstance(obs, BrowserOutputObservation)
        observation_text = str(obs)
        assert '[Action executed successfully.]' in observation_text
        assert 'File Viewer - test_image.png' in observation_text
        assert (
            'Screenshot saved to: /workspace/.browser_screenshots/screenshot_'
            in observation_text
        )

        # Check the /workspace/.browser_screenshots folder
        action_cmd = CmdRunAction(command='ls /workspace/.browser_screenshots')
        logger.info(action_cmd, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_cmd)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert isinstance(obs, CmdOutputObservation)
        assert obs.exit_code == 0
        assert 'screenshot_' in obs.content
        assert '.png' in obs.content
    finally:
        _close_test_runtime(runtime)


@pytest.mark.skipif(
    os.environ.get('TEST_RUNTIME') == 'cli',
    reason='CLIRuntime does not support browsing actions',
)
def test_download_file(temp_dir, runtime_cls, run_as_openhands):
    """Test downloading a file using the browser."""
    runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    try:
        # Create a test file to download
        test_file_content = 'This is a test file for download'
        test_file_name = 'test_download.txt'
        test_file_path = os.path.join(temp_dir, test_file_name)

        with open(test_file_path, 'w') as f:
            f.write(test_file_content)

        # Copy the file to the sandbox
        sandbox_dir = config.workspace_mount_path_in_sandbox
        runtime.copy_to(test_file_path, sandbox_dir)

        # Create a simple HTML page with a download link
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Download Test</title>
        </head>
        <body>
            <h1>Download Test Page</h1>
            <p>Click the link below to download the test file:</p>
            <a href="/workspace/{test_file_name}" download="{test_file_name}" id="download-link">Download Test File</a>
        </body>
        </html>
        """

        html_file_path = os.path.join(temp_dir, 'download_test.html')
        with open(html_file_path, 'w') as f:
            f.write(html_content)

        # Copy the HTML file to the sandbox
        runtime.copy_to(html_file_path, sandbox_dir)

        # Verify the files exist in the sandbox
        action_cmd = CmdRunAction(command='ls -alh')
        logger.info(action_cmd, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_cmd)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert isinstance(obs, CmdOutputObservation)
        assert obs.exit_code == 0
        assert test_file_name in obs.content
        assert 'download_test.html' in obs.content

        # Ensure downloads directory exists
        action_cmd = CmdRunAction(command='mkdir -p /workspace/downloads')
        logger.info(action_cmd, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_cmd)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert obs.exit_code == 0

        # Start HTTP server
        action_cmd = CmdRunAction(
            command='python3 -m http.server 8000 > server.log 2>&1 &'
        )
        logger.info(action_cmd, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_cmd)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert isinstance(obs, CmdOutputObservation)
        assert obs.exit_code == 0

        # Wait for server to start
        action_cmd = CmdRunAction(command='sleep 2')
        logger.info(action_cmd, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_cmd)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

        # Browse to the HTML page
        action_browse = BrowseURLAction(url='http://localhost:8000/download_test.html')
        logger.info(action_browse, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_browse)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

        # Verify the browser observation
        assert isinstance(obs, BrowserOutputObservation)
        assert 'http://localhost:8000/download_test.html' in obs.url
        assert not obs.error
        assert 'Download Test Page' in obs.content

        # Click the download link
        action_browse = BrowseInteractiveAction(
            browser_actions='click("download-link")'
        )
        logger.info(action_browse, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_browse)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

        # Verify the browser observation after clicking
        assert isinstance(obs, BrowserOutputObservation)
        assert not obs.error
        assert '[Action executed successfully.]' in str(obs)

        # Wait for download to complete
        action_cmd = CmdRunAction(command='sleep 3')
        logger.info(action_cmd, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_cmd)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

        # Check if the file was downloaded
        action_cmd = CmdRunAction(command='ls -la /workspace/downloads/')
        logger.info(action_cmd, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_cmd)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert isinstance(obs, CmdOutputObservation)
        assert obs.exit_code == 0
        assert test_file_name in obs.content

        # Verify the content of the downloaded file
        action_cmd = CmdRunAction(command=f'cat /workspace/downloads/{test_file_name}')
        logger.info(action_cmd, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_cmd)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert isinstance(obs, CmdOutputObservation)
        assert obs.exit_code == 0
        assert test_file_content in obs.content

        # Clean up
        action_cmd = CmdRunAction(command='pkill -f "python3 -m http.server" || true')
        logger.info(action_cmd, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_cmd)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

        action_cmd = CmdRunAction(command='rm -f server.log')
        logger.info(action_cmd, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_cmd)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    finally:
        _close_test_runtime(runtime)
