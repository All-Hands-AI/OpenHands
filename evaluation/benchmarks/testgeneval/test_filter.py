import ast
import re

from evaluation.benchmarks.testgeneval.constants import TestStatus
from evaluation.benchmarks.testgeneval.log_parsers import (
    MAP_REPO_TO_PARSER,
    parse_log_pytest,
)


def indent_text(text, indent_level):
    return '\n'.join(
        ' ' * indent_level + line if line.strip() else line for line in text.split('\n')
    )


def extract_preamble_classes_and_functions(code):
    class_pattern = re.compile(
        r'(?P<decorators>(?:^@[^\r\n]*(?:\r?\n(?:[ \t]+[^\r\n]*|^\)[^\r\n]*)*)*\r?\n)*?)'
        r'^class\s+([\w]+)(?:\([^)]*\))?:',  # the class line
        re.MULTILINE,
    )
    # Capture methods with or without decorators
    method_pattern = re.compile(r'(^(\s*@.*\s*)*^\s*def\s+[\w_]+\(.*\):)', re.MULTILINE)

    # Capture functions with or without decorators
    function_pattern = re.compile(
        r'(?P<decorators>(?:^@[^\r\n]*(?:\r?\n(?:[ \t]+[^\r\n]*|^\)[^\r\n]*)*)*\r?\n)*?)'
        r'^def\s+([\w_]+)\(.*\):',  # the function line
        re.MULTILINE,
    )

    preamble = ''
    classes = []
    test_functions = []

    current_position = 0

    def extract_class_body(code: str, start_index: int) -> tuple[str, int]:
        """
        Extracts the body of a class from the given code starting from the specified index.
        Returns the class body and the end index of the class body.
        """
        if not code or start_index < 0 or start_index >= len(code):
            raise ValueError('Invalid code or start index')

        # Split the code into lines
        lines = code[start_index:].split('\n')
        class_body_lines = []

        # Find the starting indentation level of the class definition
        class_start_line = lines[0]
        start_indent = len(class_start_line) - len(class_start_line.lstrip())

        inside_multiline_comment = False
        end_index = start_index
        for i, line in enumerate(lines[1:], start=1):
            stripped_line = line.strip()
            current_indent = len(line) - len(line.lstrip())

            # Handle multiline comments or docstrings
            if stripped_line.startswith('"""') or stripped_line.startswith("'''"):
                if inside_multiline_comment:
                    inside_multiline_comment = False
                else:
                    inside_multiline_comment = True

            if not inside_multiline_comment:
                # Stop when we reach a line with less indentation than the class definition
                if current_indent <= start_indent and stripped_line:
                    break

            # Add lines that are part of the class body
            class_body_lines.append(line)
            # Update the end index to the current line end
            end_index = start_index + len('\n'.join(lines[: i + 1])) + 1

        return code[start_index:end_index], end_index

    while current_position < len(code):
        class_match = class_pattern.search(code, current_position)
        method_match = method_pattern.search(code, current_position)

        if class_match and (
            not method_match or class_match.start() < method_match.start()
        ):
            class_name = class_match.group(0)
            class_body, end_idx = extract_class_body(code, class_match.end())
            current_position = end_idx

            methods = []
            class_prefix = class_name
            set_prefix = False
            for method_match in method_pattern.finditer(class_body):
                method_name = method_match.group()
                method_start = method_match.start()
                if not set_prefix:
                    class_prefix = class_name + class_body[:method_start]
                    set_prefix = True
                next_method = method_pattern.search(
                    class_body, method_start + len(method_name)
                )
                method_body = (
                    class_body[method_start : next_method.start()]
                    if next_method
                    else class_body[method_start:]
                )
                methods.append((method_name, method_body))

            classes.append((class_prefix, methods, class_match.start()))

        elif method_match:
            function_name = method_match.group(0)
            start_idx = method_match.start()

            # Extract the current function's indentation level
            lines = code[start_idx:].split('\n')
            current_indent = len(lines[0]) - len(lines[0].lstrip())

            next_function = function_pattern.search(
                code, start_idx + len(function_name)
            )
            while next_function and (
                class_match is None or next_function.start() < class_match.start()
            ):
                # Calculate the indentation of the next function
                next_function_start = next_function.start()
                next_line = code[next_function_start:].split('\n', 1)[0]
                next_indent = len(next_line) - len(next_line.lstrip())

                # Check if the next function is top-level
                if next_indent <= current_indent:
                    break

                # Continue searching for the next top-level function
                next_function = function_pattern.search(
                    code, next_function.start() + len(next_function.group(0))
                )

            if next_function:
                next_function_start = next_function.start()
                if class_match and next_function_start > class_match.start():
                    next_function_start = class_match.start()
                function_body = code[start_idx:next_function_start]
            else:
                function_body = code[start_idx:]

            test_functions.append((function_body, start_idx))
            current_position = start_idx + len(function_body)

        else:
            break

    if classes and test_functions:
        preamble = code[: min(classes[0][2], test_functions[0][1])]
    else:
        preamble = (
            code[: classes[0][2]]
            if classes
            else code[: test_functions[0][1]]
            if test_functions
            else code
        )

    return preamble.strip(), classes, test_functions


def filter_passing_tests(
    test_content: str, test_output: str, repo: str
) -> tuple[str, list[str], list[str]]:
    """
    Filter tests based on their execution results.
    Returns:
        Tuple containing:
        - Modified test content with only passing tests
        - List of passing test names
        - List of failing test names
    """
    # Parse test results using appropriate parser
    parser = MAP_REPO_TO_PARSER.get(repo, parse_log_pytest)
    test_results = parser(test_output)
    # Get passing and failing tests
    passing_tests = []
    failing_tests = []
    for test_name, status in test_results.items():
        if status == TestStatus.PASSED.value:
            passing_tests.append(test_name)
        else:
            failing_tests.append(test_name)

    if not passing_tests:
        return '', passing_tests, failing_tests

    # Extract test components
    preamble, classes, functions = extract_preamble_classes_and_functions(test_content)

    # Filter classes to only include passing methods
    filtered_classes = []
    for class_name, methods, start_idx in classes:
        non_fail_methods = []
        for method_name, method_body in methods:
            # Extract the base method name for matching
            method_full_name = (
                method_name.split('.')[-1].split('(')[0].strip().split(' ')[-1]
            )
            # Check if the method name is in failing_tests or if any failing_test is in the method name
            if not (
                any(method_full_name in failing_test for failing_test in failing_tests)
                or any(
                    failing_test in method_full_name for failing_test in failing_tests
                )
            ):
                non_fail_methods.append((method_name, method_body))

        if non_fail_methods:
            filtered_classes.append((class_name, non_fail_methods, start_idx))

    # Filter standalone functions
    filtered_functions = []
    for func_body, start_idx in functions:
        func_name = func_body.split('def ')[1].split('(')[0].strip()
        if any(func_name in failing_test for failing_test in failing_tests) or any(
            failing_test in func_name for failing_test in failing_tests
        ):
            continue

        filtered_functions.append((func_body, start_idx))

    # Reconstruct test content with only passing tests
    content_parts = [preamble]

    # Add filtered classes
    for class_name, methods, _ in filtered_classes:
        class_content = class_name + '\n'
        for _, method_body in methods:
            class_content += method_body + '\n'
        content_parts.append(class_content)

    # Add filtered functions
    for func_body, _ in filtered_functions:
        content_parts.append(func_body)

    return '\n\n'.join(content_parts), passing_tests, failing_tests


def filter_tests(
    test_content: str, test_output: str, repo: str
) -> tuple[str, list[str], list[str]]:
    """
    Filter tests using AST parsing to remove failing test functions from the test file.
    Non-test functions (e.g. setup or helper methods) and classes (even if all test methods are failing)
    are preserved.

    If AST processing fails (for example, because the test file cannot be parsed),
    this function falls back on the existing regex-based filtering (filter_passing_tests).

    Returns:
        Tuple containing:
         - Modified test content (as a string) containing only passing tests.
         - List of passing test names.
         - List of failing test names.
    """
    try:
        # Attempt to parse the test file using the AST.
        tree = ast.parse(test_content)

        # Parse test results using the appropriate parser.
        parser = MAP_REPO_TO_PARSER.get(repo, parse_log_pytest)
        test_results = parser(test_output)
        passing_tests = [
            name
            for name, status in test_results.items()
            if status == TestStatus.PASSED.value
        ]
        failing_tests = [
            name
            for name, status in test_results.items()
            if status != TestStatus.PASSED.value
        ]

        # Helper function to decide if a test name should be considered failing.
        def is_failing(name: str) -> bool:
            for ft in failing_tests:
                if name in ft or ft in name:
                    return True
            return False

        new_body = []
        for node in tree.body:
            # For top-level function definitions, only filter those that look like tests.
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name.startswith('test') and is_failing(node.name):
                    continue
                new_body.append(node)
            # For classes, filter out failing test methods but preserve other methods (e.g. setup).
            elif isinstance(node, ast.ClassDef):
                new_class_body = []
                for subnode in node.body:
                    if isinstance(subnode, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        # Only consider filtering if the method is a test.
                        qualified_name = f'{node.name}.{subnode.name}'
                        if is_failing(subnode.name) or is_failing(qualified_name):
                            continue
                        new_class_body.append(subnode)
                    else:
                        new_class_body.append(subnode)
                # Always include the class even if no test methods remain, as it might contain
                # setup, teardown, or other necessary logic.
                if new_class_body:
                    node.body = new_class_body
                    new_body.append(node)

            else:
                new_body.append(node)

        tree.body = new_body

        # Reconstruct the source code from the filtered AST.
        # (Requires Python 3.9+ for ast.unparse; otherwise an exception will trigger the fallback.)
        new_test_content = ast.unparse(tree)
        return new_test_content, passing_tests, failing_tests

    except Exception:
        print('AST processing failed; falling back on regex-based filtering.')
        # If AST processing fails for any reason, fall back on the original regex-based filtering.
        return filter_passing_tests(test_content, test_output, repo)
