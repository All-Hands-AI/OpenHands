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
    ErrorObservation,
    FileDownloadObservation,
)

# ============================================================================================================================
# Browsing tests, without evaluation (poetry install --without evaluation)
# For eval environments, tests need to run with poetry install
# ============================================================================================================================


# Skip all tests in this module for CLI runtime
pytestmark = pytest.mark.skipif(
    os.environ.get('TEST_RUNTIME') == 'cli',
    reason='CLIRuntime does not support browsing actions',
)


def test_browser_disabled(temp_dir, runtime_cls, run_as_openhands):
    runtime, _ = _load_runtime(
        temp_dir, runtime_cls, run_as_openhands, enable_browser=False
    )

    action_cmd = CmdRunAction(command='python3 -m http.server 8000 > server.log 2>&1 &')
    logger.info(action_cmd, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action_cmd)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})

    action_browse = BrowseURLAction(url='http://localhost:8000', return_axtree=False)
    logger.info(action_browse, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action_browse)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert isinstance(obs, ErrorObservation)
    assert 'Browser functionality is not supported or disabled' in obs.content

    _close_test_runtime(runtime)


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


def test_browser_navigation_actions(temp_dir, runtime_cls, run_as_openhands):
    """Test browser navigation actions: goto, go_back, go_forward, noop."""
    runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    try:
        # Create test HTML pages
        page1_content = """
        <!DOCTYPE html>
        <html>
        <head><title>Page 1</title></head>
        <body>
            <h1>Page 1</h1>
            <a href="page2.html" id="link-to-page2">Go to Page 2</a>
        </body>
        </html>
        """

        page2_content = """
        <!DOCTYPE html>
        <html>
        <head><title>Page 2</title></head>
        <body>
            <h1>Page 2</h1>
            <a href="page1.html" id="link-to-page1">Go to Page 1</a>
        </body>
        </html>
        """

        # Create HTML files in temp directory
        page1_path = os.path.join(temp_dir, 'page1.html')
        page2_path = os.path.join(temp_dir, 'page2.html')

        with open(page1_path, 'w') as f:
            f.write(page1_content)
        with open(page2_path, 'w') as f:
            f.write(page2_content)

        # Copy files to sandbox
        sandbox_dir = config.workspace_mount_path_in_sandbox
        runtime.copy_to(page1_path, sandbox_dir)
        runtime.copy_to(page2_path, sandbox_dir)

        # Start HTTP server
        action_cmd = CmdRunAction(
            command='python3 -m http.server 8000 > server.log 2>&1 &'
        )
        logger.info(action_cmd, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_cmd)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert obs.exit_code == 0

        # Wait for server to start
        action_cmd = CmdRunAction(command='sleep 3')
        logger.info(action_cmd, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_cmd)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

        # Test goto action
        action_browse = BrowseInteractiveAction(
            browser_actions='goto("http://localhost:8000/page1.html")',
            return_axtree=False,
        )
        logger.info(action_browse, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_browse)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

        assert isinstance(obs, BrowserOutputObservation)
        assert not obs.error
        assert 'Page 1' in obs.content
        assert 'http://localhost:8000/page1.html' in obs.url

        # Test noop action (should not change page)
        action_browse = BrowseInteractiveAction(
            browser_actions='noop(500)', return_axtree=False
        )
        logger.info(action_browse, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_browse)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

        assert isinstance(obs, BrowserOutputObservation)
        assert not obs.error
        assert 'Page 1' in obs.content
        assert 'http://localhost:8000/page1.html' in obs.url

        # Navigate to page 2
        action_browse = BrowseInteractiveAction(
            browser_actions='goto("http://localhost:8000/page2.html")',
            return_axtree=False,
        )
        logger.info(action_browse, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_browse)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

        assert isinstance(obs, BrowserOutputObservation)
        assert not obs.error
        assert 'Page 2' in obs.content
        assert 'http://localhost:8000/page2.html' in obs.url

        # Test go_back action
        action_browse = BrowseInteractiveAction(
            browser_actions='go_back()', return_axtree=False
        )
        logger.info(action_browse, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_browse)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

        assert isinstance(obs, BrowserOutputObservation)
        assert not obs.error
        assert 'Page 1' in obs.content
        assert 'http://localhost:8000/page1.html' in obs.url

        # Test go_forward action
        action_browse = BrowseInteractiveAction(
            browser_actions='go_forward()', return_axtree=False
        )
        logger.info(action_browse, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_browse)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

        assert isinstance(obs, BrowserOutputObservation)
        assert not obs.error
        assert 'Page 2' in obs.content
        assert 'http://localhost:8000/page2.html' in obs.url

        # Clean up
        action_cmd = CmdRunAction(command='pkill -f "python3 -m http.server" || true')
        logger.info(action_cmd, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_cmd)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

    finally:
        _close_test_runtime(runtime)


def test_browser_form_interactions(temp_dir, runtime_cls, run_as_openhands):
    """Test browser form interaction actions: fill, click, select_option, clear using index-based approach."""
    runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    try:
        # Create a test form page
        form_content = """
        <!DOCTYPE html>
        <html>
        <head><title>Test Form</title></head>
        <body>
            <h1>Test Form</h1>
            <form id="test-form">
                <input type="text" id="text-input" name="text" placeholder="Enter text">
                <textarea id="textarea-input" name="message" placeholder="Enter message"></textarea>
                <select id="select-input" name="option">
                    <option value="">Select an option</option>
                    <option value="option1">Option 1</option>
                    <option value="option2">Option 2</option>
                    <option value="option3">Option 3</option>
                </select>
                <button type="button" id="test-button">Test Button</button>
                <input type="submit" id="submit-button" value="Submit">
            </form>
            <div id="result"></div>
            <script>
                document.getElementById('test-button').onclick = function() {
                    document.getElementById('result').innerHTML = 'Button clicked!';
                };
            </script>
        </body>
        </html>
        """

        # Create HTML file
        form_path = os.path.join(temp_dir, 'form.html')
        with open(form_path, 'w') as f:
            f.write(form_content)

        # Copy to sandbox
        sandbox_dir = config.workspace_mount_path_in_sandbox
        runtime.copy_to(form_path, sandbox_dir)

        # Start HTTP server
        action_cmd = CmdRunAction(
            command='python3 -m http.server 8000 > server.log 2>&1 &'
        )
        logger.info(action_cmd, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_cmd)
        logger.info(obs, extra={'msg_type': 'ACTION'})
        assert obs.exit_code == 0

        # Wait for server to start
        action_cmd = CmdRunAction(command='sleep 3')
        logger.info(action_cmd, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_cmd)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

        # Navigate to form page
        action_browse = BrowseInteractiveAction(
            browser_actions='goto("http://localhost:8000/form.html")',
            return_axtree=False,  # No longer need axtree for Browser-Use
        )
        logger.info(action_browse, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_browse)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

        assert isinstance(obs, BrowserOutputObservation)
        assert not obs.error
        assert 'Test Form' in obs.content

        # Test fill action using index-based approach (index 0 for first input)
        action_browse = BrowseInteractiveAction(
            browser_actions="""
fill(0, "Hello World")
fill(1, "This is a test message")
""".strip(),
            return_axtree=False,
        )
        logger.info(action_browse, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_browse)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

        assert isinstance(obs, BrowserOutputObservation)
        # Verify the action executed successfully
        assert not obs.error, (
            f'Browser action failed with error: {obs.last_browser_action_error}'
        )

        # Verify the action was recorded
        assert 'fill' in obs.last_browser_action, (
            f'Expected fill action in browser history but got: {obs.last_browser_action}'
        )

        # Test select_option action using index-based approach (index 2 for select)
        action_browse = BrowseInteractiveAction(
            browser_actions='select_option(2, "option2")',
            return_axtree=False,
        )
        logger.info(action_browse, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_browse)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

        assert isinstance(obs, BrowserOutputObservation)
        assert not obs.error, (
            f'Select option action failed: {obs.last_browser_action_error}'
        )

        # Verify the action was executed
        assert 'select_option' in obs.last_browser_action, (
            f'Expected select_option action in browser history but got: {obs.last_browser_action}'
        )

        # Test click action using index-based approach (index 3 for button)
        action_browse = BrowseInteractiveAction(
            browser_actions='click(3)', return_axtree=False
        )
        obs = runtime.run_action(action_browse)
        assert isinstance(obs, BrowserOutputObservation)
        assert not obs.error, f'Click action failed: {obs.last_browser_action_error}'

        # Verify that the button click triggered the JavaScript and updated the result div
        # This is the actual behavior we care about, not accessibility tree updates
        assert 'Button clicked!' in obs.content, (
            f"Button click should have triggered JavaScript to show 'Button clicked!' but content is: {obs.content[:200]}..."
        )

        # Test clear action using index-based approach (index 0 for first input)
        action_browse = BrowseInteractiveAction(
            browser_actions='clear(0)', return_axtree=False
        )
        obs = runtime.run_action(action_browse)
        assert isinstance(obs, BrowserOutputObservation)
        assert not obs.error, f'Clear action failed: {obs.last_browser_action_error}'

        # Verify the action was executed
        assert 'clear' in obs.last_browser_action, (
            f'Expected clear action in browser history but got: {obs.last_browser_action}'
        )

        # Clean up
        action_cmd = CmdRunAction(command='pkill -f "python3 -m http.server" || true')
        logger.info(action_cmd, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_cmd)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

    finally:
        _close_test_runtime(runtime)


def test_browser_interactive_actions(temp_dir, runtime_cls, run_as_openhands):
    """Test browser interactive actions: scroll, hover, fill, press, focus using index-based approach."""
    runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    try:
        # Create a test page with scrollable content
        scroll_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Scroll Test</title>
            <style>
                body { margin: 0; padding: 20px; }
                .content { height: 2000px; background: linear-gradient(to bottom, #ff0000, #0000ff); }
                .hover-target {
                    width: 200px; height: 100px; background: #ccc; margin: 20px;
                    border: 2px solid #000; cursor: pointer;
                }
                .hover-target:hover { background: #ffff00; }
                #focus-input { margin: 20px; padding: 10px; font-size: 16px; }
            </style>
        </head>
        <body>
            <h1>Interactive Test Page</h1>
            <div class="hover-target" id="hover-div">Hover over me</div>
            <input type="text" id="focus-input" placeholder="Focus me and type">
            <div class="content">
                <p>This is a long scrollable page...</p>
                <p style="margin-top: 500px;">Middle content</p>
                <p style="margin-top: 500px;" id="bottom-content">Bottom content</p>
            </div>
        </body>
        </html>
        """

        # Create HTML file
        scroll_path = os.path.join(temp_dir, 'scroll.html')
        with open(scroll_path, 'w') as f:
            f.write(scroll_content)

        # Copy to sandbox
        sandbox_dir = config.workspace_mount_path_in_sandbox
        runtime.copy_to(scroll_path, sandbox_dir)

        # Start HTTP server
        action_cmd = CmdRunAction(
            command='python3 -m http.server 8000 > server.log 2>&1 &'
        )
        logger.info(action_cmd, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_cmd)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert obs.exit_code == 0

        # Wait for server to start
        action_cmd = CmdRunAction(command='sleep 3')
        logger.info(action_cmd, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_cmd)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

        # Navigate to scroll page
        action_browse = BrowseInteractiveAction(
            browser_actions='goto("http://localhost:8000/scroll.html")',
            return_axtree=False,
        )
        logger.info(action_browse, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_browse)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

        assert isinstance(obs, BrowserOutputObservation)
        assert not obs.error
        assert 'Interactive Test Page' in obs.content

        # Test scroll action
        action_browse = BrowseInteractiveAction(
            browser_actions='scroll(0, 300)',  # Scroll down 300 pixels
            return_axtree=False,
        )
        logger.info(action_browse, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_browse)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

        assert isinstance(obs, BrowserOutputObservation)
        assert not obs.error, f'Scroll action failed: {obs.last_browser_action_error}'
        # Verify the scroll action was recorded correctly
        assert 'scroll(0, 300)' in obs.last_browser_action, (
            f'Expected scroll action in browser history but got: {obs.last_browser_action}'
        )

        # Test hover action using index-based approach (index 0 for first interactive element)
        action_browse = BrowseInteractiveAction(
            browser_actions='hover(0)', return_axtree=False
        )
        logger.info(action_browse, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_browse)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

        assert isinstance(obs, BrowserOutputObservation)
        assert not obs.error, f'Hover action failed: {obs.last_browser_action_error}'

        # Test focus action using index-based approach (index 1 for input element)
        action_browse = BrowseInteractiveAction(
            browser_actions='focus(1)', return_axtree=False
        )
        logger.info(action_browse, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_browse)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

        assert isinstance(obs, BrowserOutputObservation)
        assert not obs.error, f'Focus action failed: {obs.last_browser_action_error}'

        # Test fill action (type in focused input) using index-based approach
        action_browse = BrowseInteractiveAction(
            browser_actions='fill(1, "TestValue123")',
            return_axtree=False,
        )
        logger.info(action_browse, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_browse)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

        assert isinstance(obs, BrowserOutputObservation)
        assert not obs.error, f'Fill action failed: {obs.last_browser_action_error}'

        # Test press action (for pressing individual keys) using index-based approach
        action_browse = BrowseInteractiveAction(
            browser_actions='press(1, "Backspace")',
            return_axtree=False,
        )
        logger.info(action_browse, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_browse)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

        assert isinstance(obs, BrowserOutputObservation)
        assert not obs.error, f'Press action failed: {obs.last_browser_action_error}'

        # Test multiple actions in sequence
        action_browse = BrowseInteractiveAction(
            browser_actions="""
scroll(0, -200)
noop(1000)
scroll(0, 400)
""".strip(),
            return_axtree=False,
        )
        logger.info(action_browse, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_browse)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

        assert isinstance(obs, BrowserOutputObservation)
        assert not obs.error, (
            f'Multiple actions sequence failed: {obs.last_browser_action_error}'
        )
        # Verify the last action in the sequence was recorded
        assert (
            'scroll(0, 400)' in obs.last_browser_action
            or 'noop(1000)' in obs.last_browser_action
        ), f'Expected final action from sequence but got: {obs.last_browser_action}'

        # Clean up
        action_cmd = CmdRunAction(command='pkill -f "python3 -m http.server" || true')
        logger.info(action_cmd, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_cmd)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

    finally:
        _close_test_runtime(runtime)


def test_browser_file_upload(temp_dir, runtime_cls, run_as_openhands):
    """Test browser file upload action using index-based approach."""
    runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    try:
        # Create a test file to upload
        test_file_content = 'This is a test file for upload testing.'
        test_file_path = os.path.join(temp_dir, 'upload_test.txt')
        with open(test_file_path, 'w') as f:
            f.write(test_file_content)

        # Create an upload form page
        upload_content = """
        <!DOCTYPE html>
        <html>
        <head><title>File Upload Test</title></head>
        <body>
            <h1>File Upload Test</h1>
            <form enctype="multipart/form-data">
                <input type="file" id="file-input" name="file" accept=".txt,.pdf,.png">
                <button type="button" onclick="handleUpload()">Upload File</button>
            </form>
            <div id="upload-result"></div>
            <script>
                function handleUpload() {
                    const fileInput = document.getElementById('file-input');
                    if (fileInput.files.length > 0) {
                        document.getElementById('upload-result').innerHTML =
                            'File selected: ' + fileInput.files[0].name;
                    } else {
                        document.getElementById('upload-result').innerHTML = 'No file selected';
                    }
                }
            </script>
        </body>
        </html>
        """

        # Create HTML file
        upload_path = os.path.join(temp_dir, 'upload.html')
        with open(upload_path, 'w') as f:
            f.write(upload_content)

        # Copy files to sandbox
        sandbox_dir = config.workspace_mount_path_in_sandbox
        runtime.copy_to(upload_path, sandbox_dir)
        runtime.copy_to(test_file_path, sandbox_dir)

        # Start HTTP server
        action_cmd = CmdRunAction(
            command='python3 -m http.server 8000 > server.log 2>&1 &'
        )
        logger.info(action_cmd, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_cmd)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert obs.exit_code == 0

        # Wait for server to start
        action_cmd = CmdRunAction(command='sleep 3')
        logger.info(action_cmd, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_cmd)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

        # Navigate to upload page
        action_browse = BrowseInteractiveAction(
            browser_actions='goto("http://localhost:8000/upload.html")',
            return_axtree=False,
        )
        logger.info(action_browse, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_browse)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

        assert isinstance(obs, BrowserOutputObservation)
        assert not obs.error
        assert 'File Upload Test' in obs.content

        # Test upload_file action using index-based approach (index 0 for file input)
        action_browse = BrowseInteractiveAction(
            browser_actions='upload_file(0, "/workspace/upload_test.txt")',
            return_axtree=False,
        )
        logger.info(action_browse, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_browse)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

        assert isinstance(obs, BrowserOutputObservation)
        assert not obs.error, (
            f'File upload action failed: {obs.last_browser_action_error}'
        )

        # Test clicking the upload button to trigger the JavaScript function (index 1 for button)
        action_browse = BrowseInteractiveAction(
            browser_actions='click(1)',
            return_axtree=False,
        )
        logger.info(action_browse, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_browse)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

        assert isinstance(obs, BrowserOutputObservation)
        assert not obs.error, (
            f'Upload button click failed: {obs.last_browser_action_error}'
        )

        # Check if the JavaScript function executed and updated the result div
        # This is the actual behavior we care about, not accessibility tree updates
        assert 'File selected:' in obs.content or 'upload_test.txt' in obs.content, (
            f'JavaScript upload handler should have updated the page but no result found in content: {obs.content[:200]}...'
        )

        # Clean up
        action_cmd = CmdRunAction(command='pkill -f "python3 -m http.server" || true')
        logger.info(action_cmd, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_cmd)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

    finally:
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


def test_download_file(temp_dir, runtime_cls, run_as_openhands):
    """Test downloading a file using the browser."""
    runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    try:
        # Minimal PDF content for testing
        pdf_content = b"""%PDF-1.4
        1 0 obj

        /Type /Catalog
        /Pages 2 0 R
        >>
        endobj
        2 0 obj

        /Type /Pages
        /Kids [3 0 R]
        /Count 1
        >>
        endobj
        3 0 obj

        /Type /Page
        /Parent 2 0 R
        /MediaBox [0 0 612 792]
        >>
        endobj
        xref
        0 4
        0000000000 65535 f
        0000000010 00000 n
        0000000053 00000 n
        0000000125 00000 n
        trailer

        /Size 4
        /Root 1 0 R
        >>
        startxref
        212
        %%EOF"""

        test_file_name = 'test_download.pdf'
        test_file_path = os.path.join(temp_dir, test_file_name)
        with open(test_file_path, 'wb') as f:
            f.write(pdf_content)

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
            <a href="/{test_file_name}" download="{test_file_name}" id="download-link">Download Test File</a>
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
        action_cmd = CmdRunAction(command='mkdir -p /workspace/.downloads')
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

        # Go to the PDF file url directly - this should trigger download
        file_url = f'http://localhost:8000/{test_file_name}'
        action_browse = BrowseInteractiveAction(
            browser_actions=f'goto("{file_url}")',
        )
        logger.info(action_browse, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_browse)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

        # Verify the browser observation after navigating to PDF file
        downloaded_file_name = 'file_1.pdf'
        assert isinstance(obs, FileDownloadObservation)
        assert 'Location of downloaded file:' in str(obs)
        assert downloaded_file_name in str(obs)  # File is renamed

        # Wait for download to complete
        action_cmd = CmdRunAction(command='sleep 3')
        logger.info(action_cmd, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_cmd)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

        # Check if the file was downloaded
        action_cmd = CmdRunAction(command='ls -la /workspace')
        logger.info(action_cmd, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_cmd)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert isinstance(obs, CmdOutputObservation)
        assert obs.exit_code == 0
        assert downloaded_file_name in obs.content

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
