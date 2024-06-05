import os
import re
import subprocess
import sys
import traceback
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Set

from grep_ast import TreeContext, filename_to_lang
from tree_sitter_languages import get_parser  # noqa: E402

# tree_sitter is throwing a FutureWarning
warnings.simplefilter('ignore', category=FutureWarning)


class Linter:
    def __init__(self, encoding='utf-8', root=None):
        self.encoding = encoding
        self.root = root

        self.languages = dict(
            python=self.py_lint,
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
        errors = stdout.decode()
        if process.returncode == 0:
            return  # zero exit status

        cmd = ' '.join(cmd)
        res = f'## Running: {cmd}\n\n'
        res += errors

        linenums = []
        filenames_linenums = find_filenames_and_linenums(errors, [rel_fname])
        if filenames_linenums:
            filename, linenums = next(iter(filenames_linenums.items()))
            linenums = [num - 1 for num in linenums]

        return LintResult(text=res, lines=linenums)

    def lint(self, fname, cmd=None):
        rel_fname = self.get_rel_fname(fname)
        code = Path(fname).read_text(self.encoding)

        if cmd:
            cmd = cmd.strip()
        if not cmd:
            lang = filename_to_lang(fname)
            if not lang:
                return
            if self.all_lint_cmd:
                cmd = self.all_lint_cmd
            else:
                cmd = self.languages.get(lang)

        if callable(cmd):
            linkres = cmd(fname, rel_fname, code)
        elif cmd:
            linkres = self.run_cmd(cmd, rel_fname, code)
        else:
            linkres = basic_lint(rel_fname, code)

        if not linkres:
            return

        res = '# Fix any errors below, if possible.\n\n'
        res += linkres.text
        res += '\n'
        res += tree_context(rel_fname, code, linkres.lines)

        return res

    def py_lint(self, fname, rel_fname, code):
        basic_res = basic_lint(rel_fname, code)
        compile_res = lint_python_compile(fname, code)

        fatal = 'E9,F821,F823,F831,F406,F407,F701,F702,F704,F706'
        flake8 = f'flake8 --select={fatal} --show-source --isolated'

        try:
            flake_res = self.run_cmd(flake8, rel_fname, code)
        except FileNotFoundError:
            flake_res = None

        text = ''
        lines = list()
        for res in [basic_res, compile_res, flake_res]:
            if not res:
                continue
            if text:
                text += '\n'
            text += res.text
            lines.extend(res.lines)

        if text or lines:
            return LintResult(text, lines)


@dataclass
class LintResult:
    text: str
    lines: list


def lint_python_compile(fname, code):
    try:
        compile(code, fname, 'exec')  # USE TRACEBACK BELOW HERE
        return
    except SyntaxError as err:
        lineno = getattr(err, 'lineno', None)
        end_lineno = getattr(err, 'end_lineno', lineno)

        if lineno is not None and end_lineno is not None:
            line_numbers = list(range(lineno - 1, end_lineno))
        elif lineno is not None:
            line_numbers = [lineno - 1]
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
    """
    Use tree-sitter to look for syntax errors, display them with tree context.
    """

    lang = filename_to_lang(fname)
    if not lang:
        return

    parser = get_parser(lang)
    tree = parser.parse(bytes(code, 'utf-8'))

    errors = traverse_tree(tree.root_node)
    if not errors:
        return

    return LintResult(text='', lines=errors)


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
    s = 's' if len(line_nums) > 1 else ''
    output = f'## See relevant line{s} below marked with █.\n\n'
    output += fname + ':\n'
    output += context.format()

    return output


# Traverse the tree to find errors
def traverse_tree(node):
    errors = []
    if node.type == 'ERROR' or node.is_missing:
        line_no = node.start_point[0]
        errors.append(line_no)

    for child in node.children:
        errors += traverse_tree(child)

    return errors


def find_filenames_and_linenums(text, fnames):
    """
    Search text for all occurrences of <filename>:\\d+ and make a list of them
    where <filename> is one of the filenames in the list `fnames`.
    """
    pattern = re.compile(
        r'(\b(?:' + '|'.join(re.escape(fname) for fname in fnames) + r'):\d+\b)'
    )
    matches = pattern.findall(text)
    result: Dict[str, Set[int]] = {}
    for match in matches:
        fname, linenum = match.rsplit(':', 1)
        if fname not in result:
            result[fname] = set()
        result[fname].add(int(linenum))
    return result


def main():
    """
    Main function to parse files provided as command line arguments.
    """
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
