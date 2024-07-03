import ast
import glob
import pathlib
from os.path import join as pjoin


def find_python_files(dir_path: str) -> list[str]:
    """Get all .py files recursively from a directory.

    Skips files that are obviously not from the source code, such third-party library code.

    Args:
        dir_path (str): Path to the directory.
    Returns:
        List[str]: List of .py file paths. These paths are ABSOLUTE path!
    """

    py_files = glob.glob(pjoin(dir_path, '**/*.py'), recursive=True)
    res = []
    for file in py_files:
        rel_path = file[len(dir_path) + 1 :]
        if rel_path.startswith('build'):
            continue
        if rel_path.startswith('doc'):
            # discovered this issue in 'pytest-dev__pytest'
            continue
        if rel_path.startswith('requests/packages'):
            # to walkaround issue in 'psf__requests'
            continue
        if (
            rel_path.startswith('tests/regrtest_data')
            or rel_path.startswith('tests/input')
            or rel_path.startswith('tests/functional')
        ):
            # to walkaround issue in 'pylint-dev__pylint'
            continue
        if rel_path.startswith('tests/roots') or rel_path.startswith(
            'sphinx/templates/latex'
        ):
            # to walkaround issue in 'sphinx-doc__sphinx'
            continue
        if rel_path.startswith('tests/test_runner_apps/tagged/') or rel_path.startswith(
            'django/conf/app_template/'
        ):
            # to walkaround issue in 'django__django'
            continue
        res.append(file)
    return res


def parse_python_file(file_full_path: str):
    """
    Main method to parse AST and build search index.
    Handles complication where python ast module cannot parse a file.
    """
    try:
        file_content = pathlib.Path(file_full_path).read_text()
        tree = ast.parse(file_content)
    except Exception:
        return None

    # (1) get all classes defined in the file
    classes = []
    # (2) for each class in the file, get all functions defined in the class.
    class_to_funcs = {}
    # (3) get top-level functions in the file (exclues functions defined in classes)
    top_level_funcs = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            ## class part (1): collect class info
            class_name = node.name
            start_lineno = node.lineno
            end_lineno = node.end_lineno
            # line numbers are 1-based
            classes.append((class_name, start_lineno, end_lineno))

            ## class part (2): collect function info inside this class
            class_funcs = [
                (n.name, n.lineno, n.end_lineno)
                for n in ast.walk(node)
                if isinstance(n, ast.FunctionDef)
            ]
            class_to_funcs[class_name] = class_funcs

        elif isinstance(node, ast.FunctionDef):
            function_name = node.name
            start_lineno = node.lineno
            end_lineno = node.end_lineno
            # line numbers are 1-based
            top_level_funcs.append((function_name, start_lineno, end_lineno))

    return classes, class_to_funcs, top_level_funcs
