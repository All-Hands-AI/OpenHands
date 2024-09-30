from openhands.linter import DefaultLinter, LintResult
from openhands.linter.languages.treesitter import TreesitterBasicLinter


def test_syntax_error_py_file(syntax_error_py_file):
    linter = TreesitterBasicLinter()
    result = linter.lint(syntax_error_py_file)
    print(result)
    assert isinstance(result, list) and len(result) == 1
    assert result[0] == LintResult(
        file=syntax_error_py_file,
        line=5,
        column=5,
        message='Syntax error',
    )

    assert (
        result[0].visualize()
        == (
            '2|    def foo():\n'
            '3|        print("Hello, World!")\n'
            '4|    print("Wrong indent")\n'
            '\033[91m5|    foo(\033[0m\n'  # color red
            '      ^ ERROR HERE: Syntax error\n'
            '6|'
        )
    )
    print(result[0].visualize())

    general_linter = DefaultLinter()
    general_result = general_linter.lint(syntax_error_py_file)
    # NOTE: general linter returns different result
    # because it uses flake8 first, which is different from treesitter
    assert general_result != result


def test_simple_correct_ruby_file(simple_correct_ruby_file):
    linter = TreesitterBasicLinter()
    result = linter.lint(simple_correct_ruby_file)
    assert isinstance(result, list) and len(result) == 0

    # Test that the general linter also returns the same result
    general_linter = DefaultLinter()
    general_result = general_linter.lint(simple_correct_ruby_file)
    assert general_result == result


def test_simple_incorrect_ruby_file(simple_incorrect_ruby_file):
    linter = TreesitterBasicLinter()
    result = linter.lint(simple_incorrect_ruby_file)
    print(result)
    assert isinstance(result, list) and len(result) == 2
    assert result[0] == LintResult(
        file=simple_incorrect_ruby_file,
        line=1,
        column=1,
        message='Syntax error',
    )
    print(result[0].visualize())
    assert (
        result[0].visualize()
        == (
            '\033[91m1|def foo():\033[0m\n'  # color red
            '  ^ ERROR HERE: Syntax error\n'
            '2|    print("Hello, World!")\n'
            '3|foo()'
        )
    )
    assert result[1] == LintResult(
        file=simple_incorrect_ruby_file,
        line=1,
        column=10,
        message='Syntax error',
    )
    print(result[1].visualize())
    assert (
        result[1].visualize()
        == (
            '\033[91m1|def foo():\033[0m\n'  # color red
            '           ^ ERROR HERE: Syntax error\n'
            '2|    print("Hello, World!")\n'
            '3|foo()'
        )
    )

    # Test that the general linter also returns the same result
    general_linter = DefaultLinter()
    general_result = general_linter.lint(simple_incorrect_ruby_file)
    assert general_result == result


def test_parenthesis_incorrect_ruby_file(parenthesis_incorrect_ruby_file):
    linter = TreesitterBasicLinter()
    result = linter.lint(parenthesis_incorrect_ruby_file)
    print(result)
    assert isinstance(result, list) and len(result) == 1
    assert result[0] == LintResult(
        file=parenthesis_incorrect_ruby_file,
        line=1,
        column=1,
        message='Syntax error',
    )
    print(result[0].visualize())
    assert result[0].visualize() == (
        '\033[91m1|def print_hello_world()\033[0m\n'
        '  ^ ERROR HERE: Syntax error\n'
        "2|    puts 'Hello World'"
    )

    # Test that the general linter also returns the same result
    general_linter = DefaultLinter()
    general_result = general_linter.lint(parenthesis_incorrect_ruby_file)
    assert general_result == result
