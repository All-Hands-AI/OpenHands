"""Tests for the command helper functions in function_calling.py."""

import os

import pytest
from conftest import (
    _close_test_runtime,
    _load_runtime,
)

from openhands.agenthub.readonly_agent.function_calling import (
    glob_to_cmdrun,
    grep_to_cmdrun,
)
from openhands.core.logger import openhands_logger as logger
from openhands.events.action import CmdRunAction
from openhands.events.observation import CmdOutputObservation, ErrorObservation

# Skip all tests in this file if running with CLIRuntime,
# as they depend on `rg` (ripgrep) which is not guaranteed to be available.
# The underlying ReadOnlyAgent tools (GrepTool, GlobTool) also currently depend on `rg`.
# TODO: implement a fallback version of these tools that uses `find` and `grep`.
pytestmark = pytest.mark.skipif(
    os.environ.get('TEST_RUNTIME') == 'cli',
    reason="CLIRuntime: ReadOnlyAgent's GrepTool/GlobTool tests require `rg` (ripgrep), which may not be installed.",
)


def _run_cmd_action(runtime, custom_command: str):
    action = CmdRunAction(command=custom_command)
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    assert isinstance(obs, (CmdOutputObservation, ErrorObservation))
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    return obs


def test_grep_to_cmdrun_basic():
    """Test basic pattern with no special characters."""
    cmd = grep_to_cmdrun('function', 'src')
    assert 'rg -li function' in cmd
    assert 'Below are the execution results' in cmd

    # With include parameter
    cmd = grep_to_cmdrun('error', 'src', '*.js')
    assert 'rg -li error' in cmd
    assert "--glob '*.js'" in cmd
    assert 'Below are the execution results' in cmd


def test_grep_to_cmdrun_quotes(temp_dir, runtime_cls, run_as_openhands):
    """Test patterns with different types of quotes."""
    runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    try:
        # Double quotes in pattern
        cmd = grep_to_cmdrun(r'const message = "Hello"', '/workspace')
        assert 'rg -li' in cmd

        # Verify command works by executing it on a test file
        setup_cmd = 'echo \'const message = "Hello";\' > /workspace/test_quotes.js'
        obs = _run_cmd_action(runtime, setup_cmd)
        assert obs.exit_code == 0

        obs = _run_cmd_action(runtime, cmd)
        assert obs.exit_code == 0
        assert '/workspace/test_quotes.js' in obs.content

        # Single quotes in pattern
        cmd = grep_to_cmdrun("function\\('test'\\)", '/workspace')
        assert 'rg -li' in cmd

        setup_cmd = 'echo "function(\'test\') {}" > /workspace/test_quotes2.js'
        obs = _run_cmd_action(runtime, setup_cmd)
        assert obs.exit_code == 0

        obs = _run_cmd_action(runtime, cmd)
        assert obs.exit_code == 0
        assert '/workspace/test_quotes2.js' in obs.content
    finally:
        _close_test_runtime(runtime)


def test_grep_to_cmdrun_special_chars(runtime_cls, run_as_openhands, temp_dir):
    """Test patterns with special shell characters."""
    runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    try:
        # Create test directory and files with special pattern content
        setup_cmd = """
        mkdir -p /workspace/test_special_patterns && \
        echo "testing x && y || z pattern" > /workspace/test_special_patterns/logical.txt && \
        echo "function() { return x; }" > /workspace/test_special_patterns/function.txt && \
        echo "using \\$variable here" > /workspace/test_special_patterns/dollar.txt && \
        echo "using \\`backticks\\` here" > /workspace/test_special_patterns/backticks.txt && \
        echo "line with \\n newline chars" > /workspace/test_special_patterns/newline.txt && \
        echo "matching *.js wildcard" > /workspace/test_special_patterns/wildcard.txt && \
        echo "testing x > y redirection" > /workspace/test_special_patterns/redirect.txt && \
        echo "testing a | b pipe" > /workspace/test_special_patterns/pipe.txt && \
        echo "line with #comment" > /workspace/test_special_patterns/comment.txt && \
        echo "CSS \\!important rule" > /workspace/test_special_patterns/bang.txt
        """
        obs = _run_cmd_action(runtime, setup_cmd)
        assert obs.exit_code == 0, 'Failed to set up test files'

        special_patterns = [
            r'x && y \|\| z',  # Shell logical operators (escaping pipe)
            r'function\(\) \{ return x; \}',  # Properly escaped braces and parentheses
            r'\$variable',  # Dollar sign
            # r"`backticks`",            # Backticks
            r'\\n newline',  # Escaped characters
            r'\*\.js',  # Wildcards (escaped)
            r'x > y',  # Redirection
            r'a \| b',  # Pipe (escaped)
            r'#comment',  # Hash
            # r"!important",             # Bang
        ]

        for pattern in special_patterns:
            # Generate the grep command using our helper function
            cmd = grep_to_cmdrun(pattern, '/workspace/test_special_patterns')
            assert 'rg -li' in cmd
            assert 'Below are the execution results of the search command:' in cmd

            # Execute the command
            obs = _run_cmd_action(runtime, cmd)

            # Verify the command executed successfully
            assert 'command not found' not in obs.content
            assert 'syntax error' not in obs.content
            assert 'unexpected' not in obs.content

            # Check that the pattern was found in the appropriate file
            if '&&' in pattern:
                assert 'logical.txt' in obs.content
            elif 'function' in pattern:
                assert 'function.txt' in obs.content
            elif '$variable' in pattern:
                assert 'dollar.txt' in obs.content
            # elif "backticks" in pattern:
            #     assert "backticks.txt" in obs.content
            elif '\\n newline' in pattern:
                assert 'newline.txt' in obs.content
            elif '*' in pattern:
                assert 'wildcard.txt' in obs.content
            elif '>' in pattern:
                assert 'redirect.txt' in obs.content
            elif '|' in pattern:
                assert 'pipe.txt' in obs.content
            elif '#comment' in pattern:
                assert 'comment.txt' in obs.content
            # elif "!important" in pattern:
            #     assert "bang.txt" in obs.content
    finally:
        _close_test_runtime(runtime)


def test_grep_to_cmdrun_paths_with_spaces(runtime_cls, run_as_openhands, temp_dir):
    """Test paths with spaces and special characters."""
    runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    try:
        # Create test files with content in paths with spaces
        setup_cmd = """
        mkdir -p "src/my project" "test files/unit tests" "src/special$chars" "path with spaces and $pecial ch@rs" && \
        echo "function searchablePattern() { return true; }" > "src/my project/test.js" && \
        echo "function testFunction() { return 42; }" > "test files/unit tests/test.js" && \
        echo "function specialFunction() { return null; }" > "src/special$chars/test.js" && \
        echo "function weirdFunction() { return []; }" > "path with spaces and $pecial ch@rs/test.js"
        """
        obs = _run_cmd_action(runtime, setup_cmd)
        assert obs.exit_code == 0, 'Failed to set up test files'

        special_paths = [
            'src/my project',
            'test files/unit tests',
        ]

        for path in special_paths:
            # Generate grep command and execute it
            cmd = grep_to_cmdrun('function', path)
            assert 'rg -li' in cmd

            obs = _run_cmd_action(runtime, cmd)
            assert obs.exit_code == 0, f'Grep command failed for path: {path}'
            assert 'function' in obs.content, (
                f'Expected pattern not found in output for path: {path}'
            )

            # Verify the actual file was found
            if path == 'src/my project':
                assert 'src/my project/test.js' in obs.content
            elif path == 'test files/unit tests':
                assert 'test files/unit tests/test.js' in obs.content
    finally:
        _close_test_runtime(runtime)


def test_glob_to_cmdrun_basic():
    """Test basic glob patterns."""
    cmd = glob_to_cmdrun('*.js', 'src')
    assert "rg --files src -g '*.js'" in cmd
    assert 'head -n 100' in cmd
    assert 'echo "Below are the execution results of the glob command:' in cmd

    # Default path
    cmd = glob_to_cmdrun('*.py')
    assert "rg --files . -g '*.py'" in cmd
    assert 'head -n 100' in cmd
    assert 'echo "Below are the execution results of the glob command:' in cmd


def test_glob_to_cmdrun_special_patterns(runtime_cls, run_as_openhands, temp_dir):
    """Test glob patterns with special characters."""
    runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    try:
        # Create test files matching the patterns we'll test
        setup_cmd = r"""
        mkdir -p src/components src/utils && \
        touch src/file1.js src/file2.js src/file9.js && \
        touch src/components/comp.jsx src/components/comp.tsx && \
        touch src/$special-file.js && \
        touch src/temp1.js src/temp2.js && \
        touch src/file.js src/file.ts src/file.jsx && \
        touch "src/weird\`file\`.js" && \
        touch "src/file with spaces.js"
        """
        obs = _run_cmd_action(runtime, setup_cmd)
        assert obs.exit_code == 0, 'Failed to set up test files'

        special_patterns = [
            '**/*.js',  # Double glob
            '**/{*.jsx,*.tsx}',  # Braces
            'file[0-9].js',  # Character class
            'temp?.js',  # Single character wildcard
            'file.{js,ts,jsx}',  # Multiple extensions
            'file with spaces.js',  # Spaces
        ]

        for pattern in special_patterns:
            cmd = glob_to_cmdrun(pattern, 'src')
            logger.info(f'Command: {cmd}')
            # Execute the command
            obs = _run_cmd_action(runtime, cmd)
            assert obs.exit_code == 0, f'Glob command failed for pattern: {pattern}'

            # Verify expected files are found
            if pattern == '**/*.js':
                assert 'file1.js' in obs.content
                assert 'file2.js' in obs.content
            elif pattern == '**/{*.jsx,*.tsx}':
                assert 'comp.jsx' in obs.content
                assert 'comp.tsx' in obs.content
            elif pattern == 'file[0-9].js':
                assert 'file1.js' in obs.content
                assert 'file2.js' in obs.content
                assert 'file9.js' in obs.content
            elif pattern == 'temp?.js':
                assert 'temp1.js' in obs.content
                assert 'temp2.js' in obs.content
            elif pattern == 'file.{js,ts,jsx}':
                assert 'file.js' in obs.content
                assert 'file.ts' in obs.content
                assert 'file.jsx' in obs.content
            elif pattern == 'file with spaces.js':
                assert 'file with spaces.js' in obs.content
    finally:
        _close_test_runtime(runtime)


def test_glob_to_cmdrun_paths_with_spaces(runtime_cls, run_as_openhands, temp_dir):
    """Test paths with spaces and special characters for glob command."""
    runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    try:
        # Create test directories with spaces and special characters
        setup_cmd = """
        mkdir -p "project files/src" "test results/unit tests" "weird$path/code" "path with spaces and $pecial ch@rs" && \
        touch "project files/src/file1.js" "project files/src/file2.js" && \
        touch "test results/unit tests/test1.js" "test results/unit tests/test2.js" && \
        touch "weird$path/code/weird1.js" "weird$path/code/weird2.js" && \
        touch "path with spaces and $pecial ch@rs/special1.js" "path with spaces and $pecial ch@rs/special2.js"
        """
        obs = _run_cmd_action(runtime, setup_cmd)
        assert obs.exit_code == 0, 'Failed to set up test files'

        special_paths = [
            'project files/src',
            'test results/unit tests',
        ]

        for path in special_paths:
            cmd = glob_to_cmdrun('*.js', path)

            # Execute the command
            obs = _run_cmd_action(runtime, cmd)
            assert obs.exit_code == 0, f'Glob command failed for path: {path}'

            # Verify expected files are found in each path
            if path == 'project files/src':
                assert 'file1.js' in obs.content
                assert 'file2.js' in obs.content
            elif path == 'test results/unit tests':
                assert 'test1.js' in obs.content
                assert 'test2.js' in obs.content
    finally:
        _close_test_runtime(runtime)
