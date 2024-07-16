import os

import pytest

from opendevin.runtime.plugins.agent_skills.aider import Linter, LintResult


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
    from opendevin.runtime.plugins.agent_skills.aider.linter import basic_lint

    poorly_formatted_code = """
        def foo()
            print("Hello, World!")
        print("Wrong indent")
        foo(
        """
    result = basic_lint(temp_file, poorly_formatted_code)

    assert isinstance(result, LintResult)
    assert result.text == f'{temp_file}:2'
    assert 2 in result.lines


def test_basic_lint_fail_returns_text_and_lines(temp_file):
    from opendevin.runtime.plugins.agent_skills.aider.linter import basic_lint

    poorly_formatted_code = """
        def foo()
            print("Hello, World!")
        print("Wrong indent")
        foo(
        """

    result = basic_lint(temp_file, poorly_formatted_code)

    assert isinstance(result, LintResult)
    assert result.text == f'{temp_file}:2'
    assert 2 in result.lines


def test_lint_python_compile(temp_file):
    from opendevin.runtime.plugins.agent_skills.aider.linter import lint_python_compile

    result = lint_python_compile(temp_file, "print('Hello, World!')\n")

    assert result is None


def test_lint_python_compile_fail_returns_text_and_lines(temp_file):
    from opendevin.runtime.plugins.agent_skills.aider.linter import lint_python_compile

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
