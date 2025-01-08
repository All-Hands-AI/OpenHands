import re
from typing import List, Tuple

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
        r'(^(\s*@[\w\.\(\)\', ]+\s*)*^\s*class ([\w]+)\([^)]+\):)', re.MULTILINE
    )
    # Capture methods with or without decorators
    test_method_pattern = re.compile(
        r'(^(\s*@.*\s*)*^\s*def\s+test\w+\(.*\):)', re.MULTILINE
    )

    # Capture functions with or without decorators
    test_function_pattern = re.compile(
        r'(^(\s*@.*\s*)*^\s*def\s+test\w+\(.*\):)', re.MULTILINE
    )

    preamble = ''
    classes = []
    test_functions = []

    current_position = 0

    def extract_class_body(code: str, start_index: int) -> Tuple[str, int]:
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
        method_match = test_function_pattern.search(code, current_position)

        if class_match and (
            not method_match or class_match.start() < method_match.start()
        ):
            class_name = class_match.group(0)
            class_body, end_idx = extract_class_body(code, class_match.end())
            current_position = end_idx

            methods = []
            class_prefix = class_name
            set_prefix = False
            for method_match in test_method_pattern.finditer(class_body):
                method_name = method_match.group()
                method_start = method_match.start()
                if not set_prefix:
                    class_prefix = class_name + class_body[:method_start]
                    set_prefix = True
                next_method = test_method_pattern.search(
                    class_body, method_start + len(method_name)
                )
                method_body = (
                    class_body[method_start : next_method.start()]
                    if next_method
                    else class_body[method_start:]
                )
                methods.append((method_name, method_body))

            if methods:
                classes.append((class_prefix, methods, class_match.start()))
            else:
                preamble += class_name + class_body

        elif method_match:
            function_name = method_match.group(0)
            start_idx = method_match.start()
            next_function = test_function_pattern.search(
                code, start_idx + len(function_name)
            )
            function_body = (
                code[start_idx : next_function.start()]
                if next_function
                else code[start_idx:]
            )
            test_functions.append((function_body, start_idx))
            current_position = method_match.end()

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
) -> Tuple[str, List[str], List[str]]:
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
        passing_methods = []
        for method_name, method_body in methods:
            method_full_name = method_name.split('(')[0].strip()
            if method_full_name in passing_tests:
                passing_methods.append((method_name, method_body))
        if passing_methods:
            filtered_classes.append((class_name, passing_methods, start_idx))

    # Filter standalone functions
    filtered_functions = []
    for func_body, start_idx in functions:
        func_name = func_body.split('def ')[1].split('(')[0].strip()
        if func_name in passing_tests:
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
