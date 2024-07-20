import glob
import re
import warnings
from dataclasses import dataclass
from importlib import resources
from os.path import join as pjoin
from pathlib import Path

from tree_sitter import Node
from tree_sitter_languages import get_language, get_parser

# tree_sitter is throwing a FutureWarning
warnings.simplefilter('ignore', category=FutureWarning)


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


def get_captures_for_node(node: Node, lang: str) -> list | None:
    """Get the captures for a node.

    Args:
        node (Node): The AST node.
        lang (str): The language of the AST.

    Returns:
        list: List of captures.
    """
    language = get_language(lang)
    try:
        scm_fname = resources.files(__package__).joinpath('queries', f'{lang}-tags.scm')
        # scm_fname = Path(__file__).parent.joinpath('queries', f'{lang}-tags.scm')
    except KeyError:
        return None
    query_scm = scm_fname
    query_scm_content = query_scm.read_text()
    query = language.query(query_scm_content)
    captures = query.captures(node)
    return list(captures)


def parse_file(file_full_path: str, lang: str = 'python'):
    """
    Main method to parse AST and build search index.
    Handles complication where python ast module cannot parse a file.
    """
    code_content = Path(file_full_path).read_text()

    parser = get_parser(lang)
    tree = parser.parse(bytes(code_content, 'utf-8'))

    captures = get_captures_for_node(tree.root_node, lang)

    # (1) get all classes defined in the file
    classes: list = []
    # (2) for each class in the file, get all functions defined in the class.
    class_to_funcs: dict = {}
    # (3) get top-level functions in the file (exclues functions defined in classes)
    top_level_funcs: list = []
    class_methods: list = []

    if not captures:
        return classes, class_to_funcs, top_level_funcs

    for node, tag in captures:
        if tag == 'definition.class':
            # Traverse the next node to get the class name
            class_name = node.child_by_field_name('name').text.decode('utf-8')
            # Line numbers are 1-based
            classes.append((class_name, node.start_point[0] + 1, node.end_point[0] + 1))
        elif tag == 'definition.function':
            # Traverse the next node to get the function name
            func_name = node.child_by_field_name('name').text.decode('utf-8')
            # Check there are no classes surrounding this function
            is_class_method = False
            for c in classes:
                if c[1] <= node.start_point[0] <= c[2]:
                    is_class_method = True
                    break
            if not is_class_method:
                # Line numbers are 1-based
                top_level_funcs.append(
                    (func_name, node.start_point[0] + 1, node.end_point[0] + 1)
                )
        elif tag == 'definition.method':
            # Traverse the next node to get the method name
            func_name = node.child_by_field_name('name').text.decode('utf-8')
            # Get the class name based on line number
            class_name = None
            for c in classes:
                if c[1] <= node.start_point[0] <= c[2]:
                    class_name = c[0]
                    break
            # Line numbers are 1-based
            if class_name is not None:
                if class_name not in class_to_funcs:
                    class_to_funcs[class_name] = []
                class_to_funcs[class_name].append(
                    (func_name, node.start_point[0] + 1, node.end_point[0] + 1)
                )

            class_methods.append(
                (func_name, node.start_point[0] + 1, node.end_point[0] + 1)
            )

    return classes, class_to_funcs, top_level_funcs


def get_class_signature(file_full_path: str, class_name: str, lang: str) -> str:
    """Get the class signature.

    Args:
        file_path (str): Path to the file.
        class_name (str): Name of the class.
    """
    with open(file_full_path) as f:
        code_content = f.read()

    parser = get_parser(lang)
    tree = parser.parse(bytes(code_content, 'utf-8'))

    captures = get_captures_for_node(tree.root_node, lang)
    if not captures:
        return ''

    class_node = None
    for node, tag in captures:
        if tag == 'definition.class':
            # Traverse the next node to get the class name
            if class_name == node.child_by_field_name('name').text.decode('utf-8'):
                class_node = node
                break

    if not class_node:
        return ''

    relevant_lines = extract_class_sig_from_node(node, lang)
    with open(file_full_path) as f:
        file_content_lst = f.readlines()
    result = ''
    for line in relevant_lines:
        if line == -1:
            result += '⋮...\n'
            continue
        line_content: str = file_content_lst[line - 1]
        if line_content.strip().startswith('#'):
            # this kind of comment could be left until this stage.
            # reason: # comments are not part of func body if they appear at beginning of func
            continue
        result += f'{line}|{line_content}'
    return result


def extract_class_sig_from_node(node: Node, lang: str) -> list[int]:
    """Extract the class signature from the AST.

    Args:
        class_ast (ast.ClassDef): AST of the class.

    Returns:
        The source line numbers that contains the class signature.
    """
    # STEP (1): extract the class signature
    sig_start_line = node.start_point[0] + 1
    # check if the class has a body
    body_node = None
    for child in node.children:
        if child.type == 'block':
            body_node = child
            break

    if body_node:
        # has body
        body_start_line = body_node.start_point[0] + 1
        sig_end_line = body_start_line - 1
    else:
        # no body
        sig_end_line = node.end_point[0] + 1 or sig_start_line
    assert sig_end_line is not None
    sig_lines = list(range(sig_start_line, sig_end_line + 1))

    # STEP (2): populate the method signatures and assign signatures
    # Walk through the class node to find all methods
    captures = get_captures_for_node(node, lang)
    if not captures:
        return sig_lines

    for child_node, tag in captures:
        if tag == 'definition.method':
            sig_lines.extend(extract_func_sig_from_node(child_node))
            sig_lines.append(-1)  # separator

    return sig_lines


def extract_func_sig_from_node(node: Node) -> list[int]:
    """Extract the function signature from the AST node.

    Includes the decorators, method name, and parameters.

    Args:
        func_ast (ast.FunctionDef): AST of the function.

    Returns:
        The source line numbers that contains the function signature.
    """
    func_start_line = node.start_point[0] + 1
    # Ignore decorators for now
    func_body_node = None
    for child in node.children:
        if child.type == 'block':
            func_body_node = child
            break

    # decide end line from body
    if func_body_node:
        # has body
        body_start_line = func_body_node.start_point[0] + 1
        end_line = body_start_line - 1
    else:
        # no body
        end_line = node.end_point[0] + 1 or func_start_line
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

    @staticmethod
    def collapse_to_method_level(
        result_list: list['SearchResult'], project_root: str
    ) -> str:
        """Collapse search results to method level."""
        res: dict[str, dict] = dict()  # file -> dict(method -> count)
        for r in result_list:
            if r.file_path not in res:
                res[r.file_path] = dict()
            func_str = r.func_name if r.func_name is not None else 'Not in a function'
            if func_str not in res[r.file_path]:
                res[r.file_path][func_str] = 1
            else:
                res[r.file_path][func_str] += 1
        res_str = ''
        for file_path, funcs in res.items():
            rel_path = to_relative_path(file_path, project_root)
            file_part = f'<file>{rel_path}</file>'
            for func, count in funcs.items():
                if func == 'Not in a function':
                    func_part = func
                else:
                    func_part = f' <func>{func}</func>'
                res_str += f'- {file_part}{func_part} ({count} matches)\n'
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
    """Get the code snippet in the range in the file, with line numbers.

    Args:
        file_path (str): Full path to the file.
        start (int): Start line number. (1-based)
        end (int): End line number. (1-based)
    """
    with open(file_full_path) as f:
        file_content = f.readlines()
    snippet = ''
    for i in range(start - 1, end):
        snippet += f'{i + 1}|{file_content[i]}'
    return snippet


# TODO: enable line number in the code context
def get_code_region_containing_code(
    file_full_path: str, code_str: str
) -> list[tuple[int, str]]:
    """In a file, get the region of code that contains a specific string.

    Args:
        - file_full_path: Path to the file. (absolute path)
        - code_str: The string that the function should contain.
    Returns:
        - A list of tuple, each of them is a pair of (line_no, code_snippet).
        line_no is the starting line of the matched code; code snippet is the
        source code of the searched region.
    """
    with open(file_full_path) as f:
        file_content = f.read()

    context_size = 3
    # since the code_str may contain multiple lines, let's not split the source file.

    # we want a few lines before and after the matched string. Since the matched string
    # can also contain new lines, this is a bit trickier.
    pattern = re.compile(re.escape(code_str))
    # each occurrence is a tuple of (line_no, code_snippet) (1-based line number)
    occurrences: list[tuple[int, str]] = []
    for match in pattern.finditer(file_content):
        matched_start_pos = match.start()
        # first, find the line number of the matched start position (1-based)
        matched_line_no = file_content.count('\n', 0, matched_start_pos) + 1
        # next, get a few surrounding lines as context
        search_start = match.start() - 1
        search_end = match.end() + 1
        # from the matched position, go left to find 5 new lines.
        for _ in range(context_size):
            # find the \n to the left
            left_newline = file_content.rfind('\n', 0, search_start)
            if left_newline == -1:
                # no more new line to the left
                search_start = 0
                break
            else:
                search_start = left_newline
        # go right to fine 5 new lines
        for _ in range(context_size):
            right_newline = file_content.find('\n', search_end + 1)
            if right_newline == -1:
                # no more new line to the right
                search_end = len(file_content)
                break
            else:
                search_end = right_newline

        start = max(0, search_start)
        end = min(len(file_content), search_end)
        context = file_content[start:end]

        # Split the context into lines and add line numbers
        lines = context.splitlines()
        start_line_no = file_content.count('\n', 0, start) + 1
        numbered_lines = [(start_line_no + i, line) for i, line in enumerate(lines)]

        occurrences.append(
            (
                matched_line_no,
                ''.join([f'{line_no}|{line}\n' for line_no, line in numbered_lines]),
            )
        )

    return occurrences
