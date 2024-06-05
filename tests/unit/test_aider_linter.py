import os

import pytest

from opendevin.runtime.aider.linter import Linter, LintResult


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


def test_py_lint(linter, temp_file):
    # Test py_lint method
    result = linter.py_lint(
        temp_file, linter.get_rel_fname(temp_file), "print('Hello, World!')\n"
    )

    assert result is None  # No lint errors expected for this simple code


def test_set_linter(linter):
    # Test set_linter method
    def custom_linter(fname, rel_fname, code):
        return LintResult(text='Custom Linter', lines=[1])

    linter.set_linter('custom', custom_linter)

    assert 'custom' in linter.languages
    assert linter.languages['custom'] == custom_linter


def test_basic_lint(temp_file):
    from opendevin.runtime.aider.linter import basic_lint

    result = basic_lint(temp_file, "print('Hello, World!')\n")

    assert result is None  # No basic lint errors expected for this simple code


def test_lint_python_compile(temp_file):
    from opendevin.runtime.aider.linter import lint_python_compile

    result = lint_python_compile(temp_file, "print('Hello, World!')\n")

    assert result is None  # No compile errors expected for this simple code


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
    assert '# Fix any errors below, if possible.' in errors
