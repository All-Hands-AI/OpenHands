import os
from unittest.mock import MagicMock, patch

import pytest

from openhands.runtime.plugins.agent_skills.utils.aider import Linter, LintResult


def get_parent_directory(levels=3):
    current_file = os.path.abspath(__file__)
    parent_directory = current_file
    for _ in range(levels):
        parent_directory = os.path.dirname(parent_directory)
    return parent_directory


print(f'\nRepo root folder: {get_parent_directory()}\n')


@pytest.fixture
def temp_file(tmp_path):
    # Fixture to create a temporary file
    temp_name = os.path.join(tmp_path, 'lint-test.py')
    with open(temp_name, 'w', encoding='utf-8') as tmp_file:
        tmp_file.write("""def foo():
    print("Hello, World!")
foo()
""")
    tmp_file.close()
    yield temp_name
    os.remove(temp_name)


@pytest.fixture
def temp_ruby_file_errors(tmp_path):
    # Fixture to create a temporary file
    temp_name = os.path.join(tmp_path, 'lint-test.rb')
    with open(temp_name, 'w', encoding='utf-8') as tmp_file:
        tmp_file.write("""def foo():
    print("Hello, World!")
foo()
""")
    tmp_file.close()
    yield temp_name
    os.remove(temp_name)


@pytest.fixture
def temp_ruby_file_errors_parentheses(tmp_path):
    # Fixture to create a temporary file
    temp_name = os.path.join(tmp_path, 'lint-test.rb')
    with open(temp_name, 'w', encoding='utf-8') as tmp_file:
        tmp_file.write("""def print_hello_world()\n    puts 'Hello World'\n""")
    tmp_file.close()
    yield temp_name
    os.remove(temp_name)


@pytest.fixture
def temp_ruby_file_correct(tmp_path):
    # Fixture to create a temporary file
    temp_name = os.path.join(tmp_path, 'lint-test.rb')
    with open(temp_name, 'w', encoding='utf-8') as tmp_file:
        tmp_file.write("""def foo
  puts "Hello, World!"
end
foo
""")
    tmp_file.close()
    yield temp_name
    os.remove(temp_name)


@pytest.fixture
def linter(tmp_path):
    return Linter(root=tmp_path)


@pytest.fixture
def temp_typescript_file_errors(tmp_path):
    # Fixture to create a temporary TypeScript file with errors
    temp_name = os.path.join(tmp_path, 'lint-test.ts')
    with open(temp_name, 'w', encoding='utf-8') as tmp_file:
        tmp_file.write("""function foo() {
    console.log("Hello, World!")
foo()
""")
    tmp_file.close()
    yield temp_name
    os.remove(temp_name)


@pytest.fixture
def temp_typescript_file_errors_semicolon(tmp_path):
    # Fixture to create a temporary TypeScript file with missing semicolon
    temp_name = os.path.join(tmp_path, 'lint-test.ts')
    with open(temp_name, 'w', encoding='utf-8') as tmp_file:
        tmp_file.write("""function printHelloWorld() {
    console.log('Hello World')
}""")
    tmp_file.close()
    yield temp_name
    os.remove(temp_name)


@pytest.fixture
def temp_typescript_file_correct(tmp_path):
    # Fixture to create a temporary TypeScript file with correct code
    temp_name = os.path.join(tmp_path, 'lint-test.ts')
    with open(temp_name, 'w', encoding='utf-8') as tmp_file:
        tmp_file.write("""function foo(): void {
  console.log("Hello, World!");
}
foo();
""")
    tmp_file.close()
    yield temp_name
    os.remove(temp_name)


@pytest.fixture
def temp_typescript_file_eslint_pass(tmp_path):
    temp_name = tmp_path / 'lint-test-pass.ts'
    temp_name.write_text("""
function greet(name: string): void {
  console.log(`Hello, ${name}!`);
}
greet("World");
""")
    return str(temp_name)


@pytest.fixture
def temp_typescript_file_eslint_fail(tmp_path):
    temp_name = tmp_path / 'lint-test-fail.ts'
    temp_name.write_text("""
function greet(name) {
  console.log("Hello, " + name + "!")
  var unused = "This variable is never used";
}
greet("World")
""")
    return str(temp_name)


@pytest.fixture
def temp_react_file_pass(tmp_path):
    temp_name = tmp_path / 'react-component-pass.tsx'
    temp_name.write_text("""
import React, { useState } from 'react';

interface Props {
  name: string;
}

const Greeting: React.FC<Props> = ({ name }) => {
  const [count, setCount] = useState(0);

  return (
    <div>
      <h1>Hello, {name}!</h1>
      <p>You clicked {count} times</p>
      <button onClick={() => setCount(count + 1)}>
        Click me
      </button>
    </div>
  );
};

export default Greeting;
""")
    return str(temp_name)


@pytest.fixture
def temp_react_file_fail(tmp_path):
    temp_name = tmp_path / 'react-component-fail.tsx'
    temp_name.write_text("""
import React from 'react';

const Greeting = (props) => {
  return (
    <div>
      <h1>Hello, {props.name}!</h1>
      <button onClick={() => console.log('Clicked')}>
        Click me
      </button>
    </div>
  );
};

export default Greeting;
""")
    return str(temp_name)


def test_get_rel_fname(linter, temp_file, tmp_path):
    # Test get_rel_fname method
    rel_fname = linter.get_rel_fname(temp_file)

    assert rel_fname == os.path.relpath(temp_file, tmp_path)


def test_run_cmd(linter, temp_file):
    # Test run_cmd method with a simple command
    result = linter.run_cmd('echo', temp_file, '')

    assert result is None  # echo command should return zero exit status


def test_set_linter(linter):
    # Test set_linter method
    def custom_linter(fname, rel_fname, code):
        return LintResult(text='Custom Linter', lines=[1])

    linter.set_linter('custom', custom_linter)

    assert 'custom' in linter.languages
    assert linter.languages['custom'] == custom_linter


def test_py_lint(linter, temp_file):
    # Test py_lint method
    result = linter.py_lint(
        temp_file, linter.get_rel_fname(temp_file), "print('Hello, World!')\n"
    )

    assert result is None  # No lint errors expected for this simple code


def test_py_lint_fail(linter, temp_file):
    # Test py_lint method
    result = linter.py_lint(
        temp_file, linter.get_rel_fname(temp_file), "print('Hello, World!')\n"
    )

    assert result is None


def test_basic_lint(temp_file):
    from openhands.runtime.plugins.agent_skills.utils.aider.linter import basic_lint

    poorly_formatted_code = """
        def foo()
            print("Hello, World!")
        print("Wrong indent")
        foo(
        """
    result = basic_lint(temp_file, poorly_formatted_code)

    assert isinstance(result, LintResult)
    assert result.text.startswith(f'{temp_file}:2:9')
    assert 2 in result.lines


def test_basic_lint_fail_returns_text_and_lines(temp_file):
    from openhands.runtime.plugins.agent_skills.utils.aider.linter import basic_lint

    poorly_formatted_code = """
        def foo()
            print("Hello, World!")
        print("Wrong indent")
        foo(
        """

    result = basic_lint(temp_file, poorly_formatted_code)

    assert isinstance(result, LintResult)
    assert result.text.startswith(f'{temp_file}:2:9')
    assert 2 in result.lines


def test_lint_python_compile(temp_file):
    from openhands.runtime.plugins.agent_skills.utils.aider.linter import (
        lint_python_compile,
    )

    result = lint_python_compile(temp_file, "print('Hello, World!')\n")

    assert result is None


def test_lint_python_compile_fail_returns_text_and_lines(temp_file):
    from openhands.runtime.plugins.agent_skills.utils.aider.linter import (
        lint_python_compile,
    )

    poorly_formatted_code = """
        def foo()
            print("Hello, World!")
        print("Wrong indent")
        foo(
        """
    result = lint_python_compile(temp_file, poorly_formatted_code)

    assert temp_file in result.text
    assert 1 in result.lines


def test_lint(linter, temp_file):
    result = linter.lint(temp_file)
    assert result is None


def test_lint_fail(linter, temp_file):
    # Test lint method
    with open(temp_file, 'w', encoding='utf-8') as lint_file:
        lint_file.write("""
def foo()
    print("Hello, World!")
  print("Wrong indent")
foo(
""")
    errors = linter.lint(temp_file)

    assert errors is not None


def test_lint_pass_ruby(linter, temp_ruby_file_correct):
    result = linter.lint(temp_ruby_file_correct)
    assert result is None


def test_lint_fail_ruby(linter, temp_ruby_file_errors):
    errors = linter.lint(temp_ruby_file_errors)
    assert errors is not None


def test_lint_fail_ruby_no_parentheses(linter, temp_ruby_file_errors_parentheses):
    errors = linter.lint(temp_ruby_file_errors_parentheses)
    assert errors is not None


def test_lint_pass_typescript(linter, temp_typescript_file_correct):
    if linter.ts_installed:
        with patch.object(linter, 'root', return_value=get_parent_directory()):
            result = linter.lint(temp_typescript_file_correct)
            assert result is None


def test_lint_fail_typescript(linter, temp_typescript_file_errors):
    if linter.ts_installed:
        errors = linter.lint(temp_typescript_file_errors)
        assert errors is not None


def test_lint_fail_typescript_missing_semicolon(
    linter, temp_typescript_file_errors_semicolon
):
    if linter.ts_installed:
        with patch.dict(os.environ, {'ENABLE_AUTO_LINT': 'True'}):
            errors = linter.lint(temp_typescript_file_errors_semicolon)
            assert errors is not None


def test_ts_eslint_pass(linter, temp_typescript_file_eslint_pass):
    with patch.object(linter, 'eslint_installed', return_value=True):
        with patch.object(linter, 'root', return_value=get_parent_directory()):
            with patch.object(linter, 'run_cmd') as mock_run_cmd:
                mock_run_cmd.return_value = MagicMock(text='[]')  # Empty ESLint output
                result = linter.ts_eslint(
                    temp_typescript_file_eslint_pass, 'lint-test-pass.ts', ''
                )
                assert result is None  # No lint errors expected


def test_ts_eslint_not_installed(linter, temp_typescript_file_eslint_pass):
    with patch.object(linter, 'eslint_installed', return_value=False):
        with patch.object(linter, 'root', return_value=get_parent_directory()):
            result = linter.lint(temp_typescript_file_eslint_pass)
            assert result is None  # Should return None when ESLint is not installed


def test_ts_eslint_run_cmd_error(linter, temp_typescript_file_eslint_pass):
    with patch.object(linter, 'eslint_installed', return_value=True):
        with patch.object(linter, 'run_cmd', side_effect=FileNotFoundError):
            result = linter.ts_eslint(
                temp_typescript_file_eslint_pass, 'lint-test-pass.ts', ''
            )
            assert result is None  # Should return None when run_cmd raises an exception


def test_ts_eslint_react_pass(linter, temp_react_file_pass):
    if not linter.eslint_installed:
        pytest.skip('ESLint is not installed. Skipping this test.')

    with patch.object(linter, 'eslint_installed', return_value=True):
        with patch.object(linter, 'run_cmd') as mock_run_cmd:
            mock_run_cmd.return_value = MagicMock(text='[]')  # Empty ESLint output
            result = linter.ts_eslint(
                temp_react_file_pass, 'react-component-pass.tsx', ''
            )
            assert result is None  # No lint errors expected


def test_ts_eslint_react_fail(linter, temp_react_file_fail):
    if not linter.eslint_installed:
        pytest.skip('ESLint is not installed. Skipping this test.')

    with patch.object(linter, 'run_cmd') as mock_run_cmd:
        mock_eslint_output = """[
            {
                "filePath": "react-component-fail.tsx",
                "messages": [
                    {
                        "ruleId": "react/prop-types",
                        "severity": 1,
                        "message": "Missing prop type for 'name'",
                        "line": 5,
                        "column": 22,
                        "nodeType": "Identifier",
                        "messageId": "missingPropType",
                        "endLine": 5,
                        "endColumn": 26
                    },
                    {
                        "ruleId": "no-console",
                        "severity": 1,
                        "message": "Unexpected console statement.",
                        "line": 7,
                        "column": 29,
                        "nodeType": "MemberExpression",
                        "messageId": "unexpected",
                        "endLine": 7,
                        "endColumn": 40
                    }
                ],
                "errorCount": 0,
                "warningCount": 2,
                "fixableErrorCount": 0,
                "fixableWarningCount": 0,
                "source": "..."
            }
        ]"""
        mock_run_cmd.return_value = MagicMock(text=mock_eslint_output)
        linter.root = get_parent_directory()
        result = linter.ts_eslint(temp_react_file_fail, 'react-component-fail.tsx', '')
        if not linter.eslint_installed:
            assert result is None
            return

        assert isinstance(result, LintResult)
        assert (
            "react-component-fail.tsx:5:22: Missing prop type for 'name' (react/prop-types)"
            in result.text
        )
        assert (
            'react-component-fail.tsx:7:29: Unexpected console statement. (no-console)'
            in result.text
        )
        assert 5 in result.lines
        assert 7 in result.lines


def test_ts_eslint_react_config(linter, temp_react_file_pass):
    if not linter.eslint_installed:
        pytest.skip('ESLint is not installed. Skipping this test.')

    with patch.object(linter, 'root', return_value=get_parent_directory()):
        with patch.object(linter, 'run_cmd') as mock_run_cmd:
            mock_run_cmd.return_value = MagicMock(text='[]')  # Empty ESLint output
            linter.root = get_parent_directory()
            result = linter.ts_eslint(
                temp_react_file_pass, 'react-component-pass.tsx', ''
            )
            assert result is None
            # Check if the ESLint command includes React-specific configuration
            called_cmd = mock_run_cmd.call_args[0][0]
            assert 'resolve-plugins-relative-to' in called_cmd
            # Additional assertions to ensure React configuration is present
            assert '--config /tmp/' in called_cmd


def test_ts_eslint_react_missing_semicolon(linter, tmp_path):
    if not linter.eslint_installed:
        pytest.skip('ESLint is not installed. Skipping this test.')

    temp_react_file = tmp_path / 'App.tsx'
    temp_react_file.write_text("""import React, { useState, useEffect, useCallback } from 'react'
import './App.css'

function App() {
  const [darkMode, setDarkMode] = useState(false);

  const toggleDarkMode = () => {
    setDarkMode(!darkMode);
    document.body.classList.toggle('dark-mode');
  };

  return (
    <div className={`App ${darkMode ? 'dark-mode' : ''}`}>
      <button onClick={toggleDarkMode}>
        {darkMode ? 'Light Mode' : 'Dark Mode'}
      </button>
    </div>
  )
}

export default App
""")

    linter.root = get_parent_directory()
    result = linter.ts_eslint(str(temp_react_file), str(temp_react_file), '')
    assert isinstance(result, LintResult)

    if 'JSONDecodeError' in result.text:
        linter.print_lint_result(result)
        pytest.skip(
            'ESLint returned a JSONDecodeError. This might be due to a configuration issue.'
        )

    if 'eslint-plugin-react' in result.text and "wasn't found" in result.text:
        linter.print_lint_result(result)
        pytest.skip(
            'eslint-plugin-react is not installed. This test requires the React ESLint plugin.'
        )

    assert any(
        'Missing semicolon' in message for message in result.text.split('\n')
    ), "Expected 'Missing semicolon' error not found"
    assert 1 in result.lines, 'Expected line 1 to be flagged for missing semicolon'
    assert 21 in result.lines, 'Expected line 21 to be flagged for missing semicolon'
