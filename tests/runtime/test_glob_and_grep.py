"""Tests for the command helper functions in function_calling.py."""

import shlex

from conftest import (
    _close_test_runtime,
    _load_runtime,
)

from openhands.agenthub.codeact_agent.function_calling import (
    glob_to_cmdrun,
    grep_to_cmdrun,
)
from openhands.core.logger import openhands_logger as logger
from openhands.events.action import CmdRunAction
from openhands.events.observation import CmdOutputObservation, ErrorObservation


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
    assert "grep -nr 'function' 'src'" in cmd
    assert 'echo "Below are the execution results of the grep command:' in cmd

    # With include parameter
    cmd = grep_to_cmdrun('error', 'src', '*.js')
    assert "grep -nr 'error' 'src' --include='*.js'" in cmd
    assert 'echo "Below are the execution results of the grep command:' in cmd


def test_grep_to_cmdrun_quotes(temp_dir, runtime_cls, run_as_openhands):
    """Test patterns with different types of quotes."""
    runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    try:
        # Double quotes in pattern
        cmd = grep_to_cmdrun('const message = "Hello"', '/workspace/test_quotes.js')
        assert 'grep -nr' in cmd

        # Verify command works by executing it on a test file
        setup_cmd = 'echo \'const message = "Hello";\' > /workspace/test_quotes.js'
        obs = _run_cmd_action(runtime, setup_cmd)
        assert obs.exit_code == 0

        obs = _run_cmd_action(runtime, cmd)
        assert obs.exit_code == 0
        assert 'const message = "Hello"' in obs.content

        # Single quotes in pattern
        cmd = grep_to_cmdrun("function('test')", '/workspace/test_quotes2.js')
        assert 'grep -nr' in cmd

        setup_cmd = 'echo "function(\'test\') {}" > /workspace/test_quotes2.js'
        obs = _run_cmd_action(runtime, setup_cmd)
        assert obs.exit_code == 0

        obs = _run_cmd_action(runtime, cmd)
        assert obs.exit_code == 0
        assert "function('test')" in obs.content
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
            r'x && y || z',  # Shell logical operators
            r'function() { return x; }',  # Braces and semicolons
            r'$variable',  # Dollar sign
            # r"`backticks`",               # Backticks
            r'\\n newline',  # Escaped characters
            r'*.js',  # Wildcards
            r'x > y',  # Redirection
            r'a | b',  # Pipe
            r'#comment',  # Hash
            # r"!important",                # Bang
        ]

        for pattern in special_patterns:
            # Generate the grep command using our helper function
            cmd = grep_to_cmdrun(pattern, '/workspace/test_special_patterns')
            # assert "grep -nrI" in cmd
            assert 'echo "Below are the execution results of the grep command:' in cmd

            # Execute the command
            obs = _run_cmd_action(runtime, cmd)

            # Verify the command executed successfully
            assert 'command not found' not in obs.content
            assert 'syntax error' not in obs.content
            assert 'unexpected' not in obs.content

            # Check that the pattern was found in the appropriate file
            if '&&' in pattern:
                assert 'logical.txt' in obs.content
            elif 'function()' in pattern:
                assert 'function.txt' in obs.content
            elif '$variable' in pattern:
                assert 'dollar.txt' in obs.content
            # elif "backticks" in pattern:
            #     assert "backticks.txt" in obs.content
            elif '\\n newline' in pattern:
                assert 'newline.txt' in obs.content
            elif '*.js' in pattern:
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
        special_paths = [
            'src/my project',
            'test files/unit tests',
            'src/special$chars',
            'path with spaces and $pecial ch@rs',
        ]

        for path in special_paths:
            cmd = grep_to_cmdrun('function', path)
            assert 'grep -nr' in cmd

            # Verify the command can be parsed properly
            parsed_cmd = shlex.split(cmd)
            assert len(parsed_cmd) >= 4  # Should have ["grep", "-r", "pattern", "path"]

            # Check that path is preserved when unquoted
            unquoted_path = parsed_cmd[3]
            for part in path.split('/'):
                assert part in unquoted_path
    finally:
        _close_test_runtime(runtime)


def test_glob_to_cmdrun_basic():
    """Test basic glob patterns."""
    cmd = glob_to_cmdrun('*.js', 'src')
    assert "find 'src' -type f -name '*.js'" in cmd
    assert 'sort -t "/" -k 1,1' in cmd
    assert 'echo "Below are the execution results of the glob command:' in cmd

    # Default path
    cmd = glob_to_cmdrun('*.py')
    assert "find '.' -type f -name '*.py'" in cmd
    assert 'sort -t "/" -k 1,1' in cmd
    assert 'echo "Below are the execution results of the glob command:' in cmd


def test_glob_to_cmdrun_special_patterns(runtime_cls, run_as_openhands, temp_dir):
    """Test glob patterns with special characters."""
    runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    try:
        special_patterns = [
            '**/*.js',  # Double glob
            'src/{*.jsx,*.tsx}',  # Braces
            '*$special*',  # Dollar sign
            'file[0-9].js',  # Character class
            'temp?.js',  # Single character wildcard
            'file.{js,ts,jsx}',  # Multiple extensions
            'weird`file`.js',  # Backticks
            'file with spaces.js',  # Spaces
        ]

        for pattern in special_patterns:
            cmd = glob_to_cmdrun(pattern, 'src')

            # Verify the pattern is properly quoted by checking if shlex can parse it
            parsed_cmd = shlex.split(cmd.split('|')[0])  # Just parse the find part
            assert (
                len(parsed_cmd) >= 6
            )  # Should have ["find", "path", "-type", "f", "-name", "pattern"]

            assert parsed_cmd[0] == 'find'
            assert parsed_cmd[2] == '-type'
            assert parsed_cmd[3] == 'f'
            assert parsed_cmd[4] == '-name'

            # Verify that core parts of the pattern are preserved when unquoted
            unquoted_pattern = parsed_cmd[5]
            core_pattern = (
                pattern.replace('*', '')
                .replace('?', '')
                .replace('{', '')
                .replace('}', '')
                .replace('[', '')
                .replace(']', '')
            )
            for part in core_pattern.split():
                if part and part not in ['$', '`']:
                    assert (
                        part in unquoted_pattern
                        or part.replace('/', '') in unquoted_pattern
                    )
    finally:
        _close_test_runtime(runtime)


def test_glob_to_cmdrun_paths_with_spaces(runtime_cls, run_as_openhands, temp_dir):
    """Test paths with spaces and special characters for glob command."""
    runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    try:
        special_paths = [
            'project files/src',
            'test results/unit tests',
            'weird$path/code',
            'path with spaces and $pecial ch@rs',
        ]

        for path in special_paths:
            cmd = glob_to_cmdrun('*.js', path)

            # Verify the command can be parsed properly
            parsed_cmd = shlex.split(cmd.split('|')[0])  # Just parse the find part
            assert (
                len(parsed_cmd) >= 6
            )  # Should have ["find", "path", "-type", "f", "-name", "pattern"]

            # Check that path is preserved when unquoted
            unquoted_path = parsed_cmd[1]
            for part in path.split('/'):
                assert part in unquoted_path
    finally:
        _close_test_runtime(runtime)


def test_grep_command(temp_dir, runtime_cls, run_as_openhands):
    """Test grep functionality with different patterns and options."""
    runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    try:
        # Create test files with content to grep
        setup_cmd = """
        mkdir -p test_grep_dir && \
        echo "function testFunction() { return 42; }" > test_grep_dir/test1.js && \
        echo "const errorHandler = (err) => { console.error(err); }" > test_grep_dir/test2.js && \
        echo "import React from 'react';" > test_grep_dir/component.jsx && \
        echo "class Logger { logError(msg) { console.error(msg); } }" > test_grep_dir/logger.ts && \
        echo "const user = { name: 'John Doe', age: 30 };" > "test_grep_dir/user data.js" && \
        echo "function special(x, y) { return x + y; }" > "test_grep_dir/special$chars.js"
        """
        obs = _run_cmd_action(runtime, setup_cmd)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert obs.exit_code == 0, 'Failed to set up test files'

        # Test basic grep pattern
        obs = _run_cmd_action(runtime, 'grep -nr "function" test_grep_dir')
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert obs.exit_code == 0
        assert 'test1.js' in obs.content
        assert 'function testFunction' in obs.content

        # Test grep with regex pattern
        obs = _run_cmd_action(runtime, 'grep -nr "error" test_grep_dir')
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert obs.exit_code == 0
        assert 'console.error' in obs.content
        assert 'test2.js' in obs.content
        assert 'logger.ts' in obs.content

        # Test grep with file include pattern
        obs = _run_cmd_action(
            runtime, 'grep -nr "error" test_grep_dir --include="*.js"'
        )
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert obs.exit_code == 0
        assert 'test2.js' in obs.content
        assert 'logger.ts' not in obs.content

        # Test grep with case insensitive option
        obs = _run_cmd_action(runtime, 'grep -nri "ERROR" test_grep_dir')
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert obs.exit_code == 0
        assert 'console.error' in obs.content

        # Test grep with pattern containing special characters
        obs = _run_cmd_action(runtime, 'grep -nr "\\{ return" test_grep_dir')
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert obs.exit_code == 0
        assert 'function testFunction' in obs.content
        assert 'function special' in obs.content

        # Test grep with a file path containing spaces
        obs = _run_cmd_action(runtime, 'grep -nr "John" "test_grep_dir/user data.js"')
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert obs.exit_code == 0
        assert 'John Doe' in obs.content

        # Test grep with a file path containing special characters
        obs = _run_cmd_action(
            runtime, 'grep -nr "special" "test_grep_dir/special$chars.js"'
        )
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert obs.exit_code == 0
        assert 'function special' in obs.content

        # Test grep with no results
        obs = _run_cmd_action(runtime, 'grep -nr "nonexistentpattern" test_grep_dir')
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert obs.exit_code == 1, 'grep should return non-zero when no matches found'
    finally:
        _close_test_runtime(runtime)


def test_glob_command(temp_dir, runtime_cls, run_as_openhands):
    """Test glob (find) functionality with different patterns and options."""
    runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    try:
        # Create test directory structure with special characters and spaces
        setup_cmd = """
        mkdir -p test_glob_dir/src/components && \
        mkdir -p test_glob_dir/src/utils && \
        mkdir -p "test_glob_dir/src/special chars" && \
        mkdir -p test_glob_dir/dist && \
        touch test_glob_dir/src/components/Button.jsx && \
        touch test_glob_dir/src/components/Card.jsx && \
        touch test_glob_dir/src/utils/logger.js && \
        touch test_glob_dir/src/utils/helpers.js && \
        touch "test_glob_dir/src/special chars/space file.js" && \
        touch "test_glob_dir/src/special chars/weird$file.jsx" && \
        touch test_glob_dir/src/index.js && \
        touch test_glob_dir/dist/bundle.js && \
        touch test_glob_dir/README.md && \
        touch test_glob_dir/package.json
        """
        obs = _run_cmd_action(runtime, setup_cmd)
        assert obs.exit_code == 0, 'Failed to set up test files'

        # Test basic find command (equivalent to glob)
        obs = _run_cmd_action(
            runtime, 'find "test_glob_dir" -type f -name "*.js" | sort'
        )
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert obs.exit_code == 0
        assert 'logger.js' in obs.content
        assert 'helpers.js' in obs.content
        assert 'index.js' in obs.content
        assert 'bundle.js' in obs.content
        assert 'space file.js' in obs.content
        assert 'Button.jsx' not in obs.content
        assert 'README.md' not in obs.content

        # Test find with specific path that has spaces
        obs = _run_cmd_action(
            runtime, 'find "test_glob_dir/src/special chars" -type f | sort'
        )
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert obs.exit_code == 0
        assert 'space file.js' in obs.content
        assert 'weird$file.jsx' in obs.content

        # Test find with specific path
        obs = _run_cmd_action(
            runtime, 'find "test_glob_dir/src/components" -type f -name "*.jsx" | sort'
        )
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert obs.exit_code == 0
        assert 'Button.jsx' in obs.content
        assert 'Card.jsx' in obs.content
        assert 'logger.js' not in obs.content

        # Test find with wildcard pattern
        obs = _run_cmd_action(
            runtime, 'find "test_glob_dir" -type f -name "README*" | sort'
        )
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert obs.exit_code == 0
        assert 'README.md' in obs.content

        # Test find with special character pattern
        obs = _run_cmd_action(
            runtime, 'find "test_glob_dir" -type f -name "*$*" | sort'
        )
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert obs.exit_code == 0
        assert 'weird$file.jsx' in obs.content

        # Test more complex pattern that mimics glob functionality
        obs = _run_cmd_action(
            runtime, 'find "test_glob_dir/src" -type f -path "*/utils/*.js" | sort'
        )
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert obs.exit_code == 0
        assert 'logger.js' in obs.content
        assert 'helpers.js' in obs.content
        assert 'index.js' not in obs.content
        assert 'Button.jsx' not in obs.content
    finally:
        _close_test_runtime(runtime)


def test_grep_and_find_combined(temp_dir, runtime_cls, run_as_openhands):
    """Test combining grep and find commands for advanced searching."""
    runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    try:
        # Create test files with content and special characters
        setup_cmd = """
        mkdir -p test_combined/frontend/components && \
        mkdir -p test_combined/frontend/utils && \
        mkdir -p "test_combined/frontend/special dir" && \
        mkdir -p test_combined/backend/api && \
        echo "export function Button() { return <button>Click Me</button>; }" > test_combined/frontend/components/Button.jsx && \
        echo "export function renderComponent(component) { /* implementation */ }" > test_combined/frontend/utils/render.js && \
        echo "import { logError } from './utils/logger';" > test_combined/frontend/index.js && \
        echo "function handleError(err) { console.error('API Error:', err); }" > test_combined/backend/api/error.js && \
        echo "const logger = { error: (msg) => console.error(msg) };" > test_combined/backend/api/logger.js && \
        echo "class SpecialComponent { /* handles special characters like $, &, [ ] */ }" > "test_combined/frontend/special dir/special$component.js"
        """
        obs = _run_cmd_action(runtime, setup_cmd)
        assert obs.exit_code == 0, 'Failed to set up test files'

        # Find all JS files and grep for error-related functions
        combined_cmd = (
            'find "test_combined" -type f -name "*.js" | xargs grep -l "error"'
        )
        obs = _run_cmd_action(runtime, combined_cmd)
        assert obs.exit_code == 0
        assert 'error.js' in obs.content
        assert 'logger.js' in obs.content

        # Find specific component files and check their content
        combined_cmd = 'find "test_combined/frontend" -type f -name "*.jsx" | xargs grep "function"'
        obs = _run_cmd_action(runtime, combined_cmd)
        assert obs.exit_code == 0
        assert 'Button.jsx' in obs.content
        assert 'function Button' in obs.content

        # Search in files with special characters in path
        combined_cmd = 'find "test_combined" -type f -name "*$*" | xargs grep "Special"'
        obs = _run_cmd_action(runtime, combined_cmd)
        assert obs.exit_code == 0
        assert 'SpecialComponent' in obs.content

        # Case insensitive search across all files in a directory
        combined_cmd = 'find "test_combined" -type f | xargs grep -i "ERROR"'
        obs = _run_cmd_action(runtime, combined_cmd)
        assert obs.exit_code == 0
        assert 'API Error' in obs.content
        assert 'logError' in obs.content
    finally:
        _close_test_runtime(runtime)


def test_grep_command_helper_integration(temp_dir, runtime_cls, run_as_openhands):
    """Test that grep_to_cmdrun function generates valid shell commands."""
    runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    try:
        # Create test files with content to grep
        setup_cmd = """
        mkdir -p test_grep_helper_dir && \
        echo "function testFunction() { return 42; }" > test_grep_helper_dir/test1.js && \
        echo "const message = \\"Hello, world!\\";" > test_grep_helper_dir/quotes.js && \
        echo "function with$special(x) { return x && y || z; }" > "test_grep_helper_dir/special chars.js"
        """
        obs = _run_cmd_action(runtime, setup_cmd)
        assert obs.exit_code == 0, 'Failed to set up test files'

        # Test various special patterns using the helper function
        test_patterns = [
            'function',  # Basic keyword
            'const message = "Hello"',  # Double quotes
            'return x && y',  # Logical operators
            '$special',  # Dollar sign
            'function.*return',  # Regex
            'x > y',  # Redirection
            '\\{ return',  # Escaped braces
            '*.js',  # Glob pattern in grep
        ]

        test_paths = [
            'test_grep_helper_dir',
            'test_grep_helper_dir/test1.js',
            'test_grep_helper_dir/quotes.js',
            'test_grep_helper_dir/special chars.js',
        ]

        for pattern in test_patterns:
            for path in test_paths:
                # Generate command using our helper
                grep_cmd = grep_to_cmdrun(pattern, path)

                # Execute the command
                obs = _run_cmd_action(runtime, grep_cmd)
                logger.info(
                    f'Pattern: {pattern}, Path: {path}', extra={'msg_type': 'INFO'}
                )
                logger.info(obs, extra={'msg_type': 'OBSERVATION'})

                # We don't assert on exit code because some patterns might not match,
                # but we check that the command executed without shell errors
                assert 'command not found' not in obs.content
                assert 'syntax error' not in obs.content
                assert 'unexpected' not in obs.content
    finally:
        _close_test_runtime(runtime)


def test_glob_command_helper_integration(temp_dir, runtime_cls, run_as_openhands):
    """Test that glob_to_cmdrun function generates valid shell commands."""
    runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    try:
        # Create test directory structure with special characters and spaces
        setup_cmd = """
        mkdir -p "test_glob_helper/normal/src" && \
        mkdir -p "test_glob_helper/special chars/src" && \
        touch "test_glob_helper/normal/src/file1.js" && \
        touch "test_glob_helper/normal/src/file2.jsx" && \
        touch "test_glob_helper/special chars/src/weird$file.js" && \
        touch "test_glob_helper/special chars/src/space file.tsx"
        """
        obs = _run_cmd_action(runtime, setup_cmd)
        assert obs.exit_code == 0, 'Failed to set up test files'

        # Test various special patterns using the helper function
        test_patterns = [
            '*.js',  # Basic glob
            'file*.js*',  # Wildcard in middle and end
            '*$*.js',  # Dollar sign
            'space file.tsx',  # Spaces
            'file{1,2}.js*',  # Braces
            '[a-z]*.js',  # Character class
            'weird$*',  # Special character
        ]

        test_paths = [
            'test_glob_helper',
            'test_glob_helper/normal',
            'test_glob_helper/normal/src',
            'test_glob_helper/special chars',
            'test_glob_helper/special chars/src',
        ]

        for pattern in test_patterns:
            for path in test_paths:
                # Generate command using our helper
                glob_cmd = glob_to_cmdrun(pattern, path)

                # Execute the command
                obs = _run_cmd_action(runtime, glob_cmd)
                logger.info(
                    f'Pattern: {pattern}, Path: {path}', extra={'msg_type': 'INFO'}
                )
                logger.info(obs, extra={'msg_type': 'OBSERVATION'})

                # Check that the command executed without shell errors
                assert 'command not found' not in obs.content
                assert 'syntax error' not in obs.content
                assert 'unexpected' not in obs.content
    finally:
        _close_test_runtime(runtime)
