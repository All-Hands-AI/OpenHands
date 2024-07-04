import ast
import glob
from dataclasses import dataclass
from os.path import join as pjoin
from pathlib import Path


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
        file_content = Path(file_full_path).read_text()
        tree = ast.parse(file_content)
    except Exception:
        return None

    # (1) get all classes defined in the file
    classes = []
    # (2) for each class in the file, get all functions defined in the class.
    class_to_funcs = {}
    # (3) get top-level functions in the file (exclues functions defined in classes)
    top_level_funcs = []

    function_nodes_in_class = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            ## class part (1): collect class info
            class_name = node.name
            start_lineno = node.lineno
            end_lineno = node.end_lineno
            # line numbers are 1-based
            classes.append((class_name, start_lineno, end_lineno))

            ## class part (2): collect function info inside this class
            class_funcs = []
            for n in ast.walk(node):
                if isinstance(n, ast.FunctionDef):
                    class_funcs.append((n.name, n.lineno, n.end_lineno))
                    function_nodes_in_class.append(n)
            class_to_funcs[class_name] = class_funcs

        # top-level functions, excluding functions defined in classes
        elif isinstance(node, ast.FunctionDef) and node not in function_nodes_in_class:
            function_name = node.name
            start_lineno = node.lineno
            end_lineno = node.end_lineno
            # line numbers are 1-based
            top_level_funcs.append((function_name, start_lineno, end_lineno))

    return classes, class_to_funcs, top_level_funcs


def get_class_signature(file_full_path: str, class_name: str) -> str:
    """Get the class signature.

    Args:
        file_path (str): Path to the file.
        class_name (str): Name of the class.
    """
    with open(file_full_path) as f:
        file_content = f.read()

    tree = ast.parse(file_content)
    relevant_lines = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            # we reached the target class
            relevant_lines = extract_class_sig_from_ast(node)
            break
    if not relevant_lines:
        return ''
    else:
        with open(file_full_path) as f:
            file_content_lst = f.readlines()
        result = ''
        for line in relevant_lines:
            line_content: str = file_content_lst[line - 1]
            if line_content.strip().startswith('#'):
                # this kind of comment could be left until this stage.
                # reason: # comments are not part of func body if they appear at beginning of func
                continue
            result += line_content
        return result


def extract_class_sig_from_ast(class_ast: ast.ClassDef) -> list[int]:
    """Extract the class signature from the AST.

    Args:
        class_ast (ast.ClassDef): AST of the class.

    Returns:
        The source line numbers that contains the class signature.
    """
    # STEP (1): extract the class signature
    sig_start_line = class_ast.lineno
    if class_ast.body:
        # has body
        body_start_line = class_ast.body[0].lineno
        sig_end_line = body_start_line - 1
    else:
        # no body
        sig_end_line = class_ast.end_lineno or sig_start_line
    assert sig_end_line is not None
    sig_lines = list(range(sig_start_line, sig_end_line + 1))

    # STEP (2): extract the function signatures and assign signatures
    for stmt in class_ast.body:
        if isinstance(stmt, ast.FunctionDef):
            sig_lines.extend(extract_func_sig_from_ast(stmt))
        elif isinstance(stmt, ast.Assign):
            # for Assign, skip some useless cases where the assignment is to create docs
            stmt_str_format = ast.dump(stmt)
            if '__doc__' in stmt_str_format:
                continue
            # otherwise, Assign is easy to handle
            assert stmt.end_lineno is not None
            assign_range = list(range(stmt.lineno, stmt.end_lineno + 1))
            sig_lines.extend(assign_range)

    return sig_lines


def extract_func_sig_from_ast(func_ast: ast.FunctionDef) -> list[int]:
    """Extract the function signature from the AST node.

    Includes the decorators, method name, and parameters.

    Args:
        func_ast (ast.FunctionDef): AST of the function.

    Returns:
        The source line numbers that contains the function signature.
    """
    func_start_line = func_ast.lineno
    if func_ast.decorator_list:
        # has decorators
        decorator_start_lines = [d.lineno for d in func_ast.decorator_list]
        decorator_first_line = min(decorator_start_lines)
        func_start_line = min(decorator_first_line, func_start_line)
    # decide end line from body
    if func_ast.body:
        # has body
        body_start_line = func_ast.body[0].lineno
        end_line = body_start_line - 1
    else:
        # no body
        end_line = func_ast.end_lineno or func_start_line
    assert end_line is not None
    return list(range(func_start_line, end_line + 1))


@dataclass
class SearchResult:
    """Dataclass to hold search results."""

    file_path: str  # absolute path
    class_name: str | None
    func_name: str | None
    code: str

    def to_tagged_upto_file(self, project_root: str):
        """Convert the search result to a tagged string, upto file path."""
        rel_path = to_relative_path(self.file_path, project_root)
        file_part = f'<file>{rel_path}</file>'
        return file_part

    def to_tagged_upto_class(self, project_root: str):
        """Convert the search result to a tagged string, upto class."""
        prefix = self.to_tagged_upto_file(project_root)
        class_part = (
            f'<class>{self.class_name}</class>' if self.class_name is not None else ''
        )
        return f'{prefix}\n{class_part}'

    def to_tagged_upto_func(self, project_root: str):
        """Convert the search result to a tagged string, upto function."""
        prefix = self.to_tagged_upto_class(project_root)
        func_part = (
            f' <func>{self.func_name}</func>' if self.func_name is not None else ''
        )
        return f'{prefix}{func_part}'

    def to_tagged_str(self, project_root: str):
        """Convert the search result to a tagged string."""
        prefix = self.to_tagged_upto_func(project_root)
        code_part = f'<code>\n{self.code}\n</code>'
        return f'{prefix}\n{code_part}'

    @staticmethod
    def collapse_to_file_level(
        result_list: list['SearchResult'], project_root: str
    ) -> str:
        """Collapse search results to file level."""
        res = dict()  # file -> count
        for r in result_list:
            if r.file_path not in res:
                res[r.file_path] = 1
            else:
                res[r.file_path] += 1
        res_str = ''
        for file_path, count in res.items():
            rel_path = to_relative_path(file_path, project_root)
            file_part = f'<file>{rel_path}</file>'
            res_str += f'- {file_part} ({count} matches)\n'
        return res_str


def to_relative_path(file_path: str, project_root: str) -> str:
    """Convert an absolute path to a path relative to the project root.

    Args:
        - file_path (str): The absolute path.
        - project_root (str): Absolute path of the project root dir.

    Returns:
        The relative path.
    """
    if Path(file_path).is_absolute():
        return str(Path(file_path).relative_to(project_root))
    else:
        return file_path


def get_code_snippets(file_full_path: str, start: int, end: int) -> str:
    """Get the code snippet in the range in the file, without line numbers.

    Args:
        file_path (str): Full path to the file.
        start (int): Start line number. (1-based)
        end (int): End line number. (1-based)
    """
    with open(file_full_path) as f:
        file_content = f.readlines()
    snippet = ''
    for i in range(start - 1, end):
        snippet += file_content[i]
    return snippet
