import os
import subprocess
import sys
import traceback
import warnings
from dataclasses import dataclass
from pathlib import Path

from grep_ast import TreeContext, filename_to_lang
from tree_sitter_languages import get_parser  # noqa: E402

# tree_sitter is throwing a FutureWarning
warnings.simplefilter('ignore', category=FutureWarning)


@dataclass
class LintResult:
    text: str
    lines: list


class Linter:
    def __init__(self, encoding='utf-8', root=None):
        self.encoding = encoding
        self.root = root

        self.languages = dict(
            python=self.py_lint,
            javascript=self.ts_lint,
            typescript=self.ts_lint,
        )
        self.all_lint_cmd = None

    def set_linter(self, lang, cmd):
        if lang:
            self.languages[lang] = cmd
            return

        self.all_lint_cmd = cmd

    def get_rel_fname(self, fname):
        if self.root:
            return os.path.relpath(fname, self.root)
        else:
            return fname

    def run_cmd(self, cmd, rel_fname, code):
        cmd += ' ' + rel_fname
        cmd = cmd.split()

        process = subprocess.Popen(
            cmd, cwd=self.root, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        )
        stdout, _ = process.communicate()
        errors = stdout.decode().strip()
        self.returncode = process.returncode
        if self.returncode == 0:
            return  # zero exit status

        cmd = ' '.join(cmd)
        res = ''
        res += errors
        line_num = extract_error_line_from(res)
        return LintResult(text=res, lines=[line_num])

    def get_abs_fname(self, fname):
        if os.path.isabs(fname):
            return fname
        elif os.path.isfile(fname):
            rel_fname = self.get_rel_fname(fname)
            return os.path.abspath(rel_fname)
        else:  # if a temp file
            return self.get_rel_fname(fname)

    def lint(self, fname, cmd=None) -> LintResult | None:
        code = Path(fname).read_text(self.encoding)
        absolute_fname = self.get_abs_fname(fname)
        if cmd:
            cmd = cmd.strip()
        if not cmd:
            lang = filename_to_lang(fname)
            if not lang:
                return None
            if self.all_lint_cmd:
                cmd = self.all_lint_cmd
            else:
                cmd = self.languages.get(lang)
        if callable(cmd):
            linkres = cmd(fname, absolute_fname, code)
        elif cmd:
            linkres = self.run_cmd(cmd, absolute_fname, code)
        else:
            linkres = basic_lint(absolute_fname, code)
        return linkres

    def flake_lint(self, rel_fname, code):
        fatal = 'F821,F822,F831,E112,E113,E999,E902'
        flake8 = f'flake8 --select={fatal} --isolated'

        try:
            flake_res = self.run_cmd(flake8, rel_fname, code)
        except FileNotFoundError:
            flake_res = None
        return flake_res

    def py_lint(self, fname, rel_fname, code):
        error = self.flake_lint(rel_fname, code)
        if not error:
            error = lint_python_compile(fname, code)
        if not error:
            error = basic_lint(rel_fname, code)
        return error

    # TODO: fix this with a correct config file, that does NOT rely on frontend!
    def eslint_lint(self, rel_fname, code):
        eslint_config_path = f'{self.root}/frontend/.eslintrc'
        eslint = f'npx eslint --config {eslint_config_path}'  # must be npx!
        try:
            eslint_res = self.run_cmd(eslint, rel_fname, code)
            if eslint_res and 'Oops' in eslint_res.text:
                eslint_res = None
        except FileNotFoundError:
            eslint_res = None
        return eslint_res

    def ts_lint(self, fname, rel_fname, code):
        # TODO: only use basic_lint for now, until we have a config file
        # error = self.eslint_lint(fname, code)
        # if not error:
        #     error = basic_lint(rel_fname, code)
        error = basic_lint(rel_fname, code)
        return error


def lint_python_compile(fname, code):
    try:
        compile(code, fname, 'exec')  # USE TRACEBACK BELOW HERE
        return
    except IndentationError as err:
        end_lineno = getattr(err, 'end_lineno', err.lineno)
        if isinstance(end_lineno, int):
            line_numbers = list(range(end_lineno - 1, end_lineno))
        else:
            line_numbers = []

        tb_lines = traceback.format_exception(type(err), err, err.__traceback__)
        last_file_i = 0

        target = '# USE TRACEBACK'
        target += ' BELOW HERE'
        for i in range(len(tb_lines)):
            if target in tb_lines[i]:
                last_file_i = i
                break
        tb_lines = tb_lines[:1] + tb_lines[last_file_i + 1 :]

    res = ''.join(tb_lines)
    return LintResult(text=res, lines=line_numbers)


def basic_lint(fname, code):
    """Use tree-sitter to look for syntax errors, display them with tree context."""
    lang = filename_to_lang(fname)
    if not lang:
        return

    parser = get_parser(lang)
    tree = parser.parse(bytes(code, 'utf-8'))

    errors = traverse_tree(tree.root_node)
    if not errors:
        return

    error_messages = [
        f'{fname}:{line}:{col}: {error_details}' for line, col, error_details in errors
    ]
    return LintResult(
        text='\n'.join(error_messages), lines=[line for line, _, _ in errors]
    )


def extract_error_line_from(lint_error):
    first_error_line = 0
    for line in lint_error.splitlines(True):
        if line.strip():
            # The format of the error message is: <filename>:<line>:<column>: <error code> <error message>
            parts = line.split(':')
            if len(parts) >= 2:
                try:
                    first_error_line = int(parts[1])
                    break
                except ValueError:
                    continue
    return first_error_line


def tree_context(fname, code, line_nums):
    context = TreeContext(
        fname,
        code,
        color=False,
        line_number=True,
        child_context=False,
        last_line=False,
        margin=0,
        mark_lois=True,
        loi_pad=3,
        # header_max=30,
        show_top_of_file_parent_scope=False,
    )
    line_nums = set(line_nums)
    context.add_lines_of_interest(line_nums)
    context.add_context()
    output = context.format()

    return output


def traverse_tree(node):
    """Traverses the tree to find errors"""
    errors = []
    if node.type == 'ERROR' or node.is_missing:
        line_no = node.start_point[0] + 1
        col_no = node.start_point[1] + 1
        error_type = 'Missing node' if node.is_missing else 'Syntax error'
        errors.append((line_no, col_no, error_type))

    for child in node.children:
        errors += traverse_tree(child)

    return errors


def main():
    """Main function to parse files provided as command line arguments."""
    if len(sys.argv) < 2:
        print('Usage: python linter.py <file1> <file2> ...')
        sys.exit(1)

    linter = Linter(root=os.getcwd())
    for file_path in sys.argv[1:]:
        errors = linter.lint(file_path)
        if errors:
            print(errors)


if __name__ == '__main__':
    main()
