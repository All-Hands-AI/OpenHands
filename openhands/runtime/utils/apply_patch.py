#!/usr/bin/env python3
"""
Apply patch utility for OpenHands runtime environments.

This utility implements a custom diff/patch format that allows agents to apply
code changes using a structured format. The format is designed to be more
reliable than traditional unified diff formats by using context-based matching
instead of line numbers.

Usage:
    apply_patch <<EOF
    *** Begin Patch
    *** Update File: path/to/file.py
    [context_before]
    - [old_code]
    + [new_code]
    [context_after]
    *** End Patch
    EOF
"""

import pathlib
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional, Union


class DiffError(Exception):
    """Exception raised when patch parsing or application fails."""

    pass


class ActionType(Enum):
    """Types of file operations supported by the patch format."""

    ADD = 'add'
    UPDATE = 'update'
    DELETE = 'delete'


# --------------------------------------------------------------------------- #
# Helper dataclasses used while parsing patches
# --------------------------------------------------------------------------- #
@dataclass
class Chunk:
    orig_index: int = -1
    del_lines: list[str] = field(default_factory=list)
    ins_lines: list[str] = field(default_factory=list)


@dataclass
class PatchAction:
    type: ActionType
    new_file: Optional[str] = None
    chunks: list[Chunk] = field(default_factory=list)
    move_path: Optional[str] = None


@dataclass
class Patch:
    actions: dict[str, PatchAction] = field(default_factory=dict)


@dataclass
class FileChange:
    type: ActionType
    old_content: Optional[str] = None
    new_content: Optional[str] = None
    move_path: Optional[str] = None


@dataclass
class Commit:
    changes: dict[str, FileChange] = field(default_factory=dict)


# --------------------------------------------------------------------------- #
# Patch text parser
# --------------------------------------------------------------------------- #
@dataclass
class Parser:
    current_files: dict[str, str]
    lines: list[str]
    index: int = 0
    patch: Patch = field(default_factory=Patch)
    fuzz: int = 0

    # ------------- low-level helpers -------------------------------------- #
    def _cur_line(self) -> str:
        if self.index >= len(self.lines):
            raise DiffError('Unexpected end of input while parsing patch')
        return self.lines[self.index]

    @staticmethod
    def _norm(line: str) -> str:
        """Strip CR so comparisons work for both LF and CRLF input."""
        return line.rstrip('\r')

    # ------------- scanning convenience ----------------------------------- #
    def is_done(self, prefixes: Optional[tuple[str, ...]] = None) -> bool:
        if self.index >= len(self.lines):
            return True
        if (
            prefixes
            and len(prefixes) > 0
            and self._norm(self._cur_line()).startswith(prefixes)
        ):
            return True
        return False

    def startswith(self, prefix: Union[str, tuple[str, ...]]) -> bool:
        return self._norm(self._cur_line()).startswith(prefix)

    def read_str(self, prefix: str) -> str:
        """
        Consume the current line if it starts with *prefix* and return the text
        **after** the prefix. Raises if prefix is empty.
        """
        if prefix == '':
            raise ValueError('read_str() requires a non-empty prefix')
        if self._norm(self._cur_line()).startswith(prefix):
            text = self._cur_line()[len(prefix) :]
            self.index += 1
            return text
        return ''

    def read_line(self) -> str:
        """Return the current raw line and advance."""
        line = self._cur_line()
        self.index += 1
        return line

    # ------------- public entry point -------------------------------------- #
    def parse(self) -> None:
        while not self.is_done(('*** End Patch',)):
            # ---------- UPDATE ---------- #
            path = self.read_str('*** Update File: ')
            if path:
                if path in self.patch.actions:
                    raise DiffError(f'Duplicate update for file: {path}')
                move_to = self.read_str('*** Move to: ')
                if path not in self.current_files:
                    raise DiffError(f'Update File Error - missing file: {path}')
                text = self.current_files[path]
                action = self._parse_update_file(text)
                action.move_path = move_to or None
                self.patch.actions[path] = action
                continue

            # ---------- DELETE ---------- #
            path = self.read_str('*** Delete File: ')
            if path:
                if path in self.patch.actions:
                    raise DiffError(f'Duplicate delete for file: {path}')
                if path not in self.current_files:
                    raise DiffError(f'Delete File Error - missing file: {path}')
                self.patch.actions[path] = PatchAction(type=ActionType.DELETE)
                continue

            # ---------- ADD ---------- #
            path = self.read_str('*** Add File: ')
            if path:
                if path in self.patch.actions:
                    raise DiffError(f'Duplicate add for file: {path}')
                if path in self.current_files:
                    raise DiffError(f'Add File Error - file already exists: {path}')
                self.patch.actions[path] = self._parse_add_file()
                continue

            raise DiffError(f'Unknown line while parsing: {self._cur_line()}')

        if not self.startswith('*** End Patch'):
            raise DiffError('Missing *** End Patch sentinel')
        self.index += 1  # consume sentinel

    # ------------- section parsers ---------------------------------------- #
    def _parse_update_file(self, text: str) -> PatchAction:
        action = PatchAction(type=ActionType.UPDATE)
        lines = text.split('\n')
        index = 0
        while not self.is_done(
            (
                '*** End Patch',
                '*** Update File:',
                '*** Delete File:',
                '*** Add File:',
                '*** End of File',
            )
        ):
            def_str = self.read_str('@@ ')
            section_str = ''
            if not def_str and self._norm(self._cur_line()) == '@@':
                section_str = self.read_line()

            if not (def_str or section_str or index == 0):
                raise DiffError(f'Invalid line in update section:\n{self._cur_line()}')

            if def_str.strip():
                found = False
                if def_str not in lines[:index]:
                    for i, s in enumerate(lines[index:], index):
                        if s == def_str:
                            index = i + 1
                            found = True
                            break
                if not found and def_str.strip() not in [
                    s.strip() for s in lines[:index]
                ]:
                    for i, s in enumerate(lines[index:], index):
                        if s.strip() == def_str.strip():
                            index = i + 1
                            self.fuzz += 1
                            found = True
                            break

            next_ctx, chunks, end_idx, eof = peek_next_section(self.lines, self.index)
            new_index, fuzz = find_context(lines, next_ctx, index, eof)
            if new_index == -1:
                ctx_txt = '\n'.join(next_ctx)
                raise DiffError(
                    f'Invalid {"EOF " if eof else ""}context at {index}:\n{ctx_txt}'
                )
            self.fuzz += fuzz
            for ch in chunks:
                ch.orig_index += new_index
                action.chunks.append(ch)
            index = new_index + len(next_ctx)
            self.index = end_idx
        return action

    def _parse_add_file(self) -> PatchAction:
        lines: list[str] = []
        while not self.is_done(
            ('*** End Patch', '*** Update File:', '*** Delete File:', '*** Add File:')
        ):
            s = self.read_line()
            if not s.startswith('+'):
                raise DiffError(f"Invalid Add File line (missing '+'): {s}")
            lines.append(s[1:])  # strip leading '+'
        return PatchAction(type=ActionType.ADD, new_file='\n'.join(lines))


# --------------------------------------------------------------------------- #
# Helper functions
# --------------------------------------------------------------------------- #
def find_context_core(
    lines: list[str], context: list[str], start: int
) -> tuple[int, int]:
    if not context:
        return start, 0

    for i in range(start, len(lines)):
        if lines[i : i + len(context)] == context:
            return i, 0
    for i in range(start, len(lines)):
        if [s.rstrip() for s in lines[i : i + len(context)]] == [
            s.rstrip() for s in context
        ]:
            return i, 1
    for i in range(start, len(lines)):
        if [s.strip() for s in lines[i : i + len(context)]] == [
            s.strip() for s in context
        ]:
            return i, 100
    return -1, 0


def find_context(
    lines: list[str], context: list[str], start: int, eof: bool
) -> tuple[int, int]:
    if eof:
        new_index, fuzz = find_context_core(lines, context, len(lines) - len(context))
        if new_index != -1:
            return new_index, fuzz
        new_index, fuzz = find_context_core(lines, context, start)
        return new_index, fuzz + 10_000
    return find_context_core(lines, context, start)


def peek_next_section(
    lines: list[str], index: int
) -> tuple[list[str], list[Chunk], int, bool]:
    old: list[str] = []
    del_lines: list[str] = []
    ins_lines: list[str] = []
    chunks: list[Chunk] = []
    mode = 'keep'
    orig_index = index

    while index < len(lines):
        s = lines[index]
        if s.startswith(
            (
                '@@',
                '*** End Patch',
                '*** Update File:',
                '*** Delete File:',
                '*** Add File:',
                '*** End of File',
            )
        ):
            break
        if s == '***':
            break
        if s.startswith('***'):
            raise DiffError(f'Invalid Line: {s}')
        index += 1

        last_mode = mode
        if s == '':
            s = ' '
        if s[0] == '+':
            mode = 'add'
        elif s[0] == '-':
            mode = 'delete'
        elif s[0] == ' ':
            mode = 'keep'
        else:
            raise DiffError(f'Invalid Line: {s}')
        s = s[1:]

        if mode == 'keep' and last_mode != mode:
            if ins_lines or del_lines:
                chunks.append(
                    Chunk(
                        orig_index=len(old) - len(del_lines),
                        del_lines=del_lines,
                        ins_lines=ins_lines,
                    )
                )
                del_lines, ins_lines = [], []

        if mode == 'delete':
            del_lines.append(s)
            old.append(s)
        elif mode == 'add':
            ins_lines.append(s)
        elif mode == 'keep':
            old.append(s)

    if ins_lines or del_lines:
        chunks.append(
            Chunk(
                orig_index=len(old) - len(del_lines),
                del_lines=del_lines,
                ins_lines=ins_lines,
            )
        )

    if index < len(lines) and lines[index] == '*** End of File':
        index += 1
        return old, chunks, index, True

    if index == orig_index:
        raise DiffError('Nothing in this section')
    return old, chunks, index, False


# --------------------------------------------------------------------------- #
# Patch → Commit and Commit application
# --------------------------------------------------------------------------- #
def _get_updated_file(text: str, action: PatchAction, path: str) -> str:
    if action.type is not ActionType.UPDATE:
        raise DiffError('_get_updated_file called with non-update action')
    orig_lines = text.split('\n')
    dest_lines: list[str] = []
    orig_index = 0

    for chunk in action.chunks:
        if chunk.orig_index > len(orig_lines):
            raise DiffError(
                f'{path}: chunk.orig_index {chunk.orig_index} exceeds file length'
            )
        if orig_index > chunk.orig_index:
            raise DiffError(
                f'{path}: overlapping chunks at {orig_index} > {chunk.orig_index}'
            )

        dest_lines.extend(orig_lines[orig_index : chunk.orig_index])
        orig_index = chunk.orig_index

        dest_lines.extend(chunk.ins_lines)
        orig_index += len(chunk.del_lines)

    dest_lines.extend(orig_lines[orig_index:])
    return '\n'.join(dest_lines)


def patch_to_commit(patch: Patch, orig: dict[str, str]) -> Commit:
    commit = Commit()
    for path, action in patch.actions.items():
        if action.type is ActionType.DELETE:
            commit.changes[path] = FileChange(
                type=ActionType.DELETE, old_content=orig[path]
            )
        elif action.type is ActionType.ADD:
            if action.new_file is None:
                raise DiffError('ADD action without file content')
            commit.changes[path] = FileChange(
                type=ActionType.ADD, new_content=action.new_file
            )
        elif action.type is ActionType.UPDATE:
            new_content = _get_updated_file(orig[path], action, path)
            commit.changes[path] = FileChange(
                type=ActionType.UPDATE,
                old_content=orig[path],
                new_content=new_content,
                move_path=action.move_path,
            )
    return commit


# --------------------------------------------------------------------------- #
# User-facing helpers
# --------------------------------------------------------------------------- #
def text_to_patch(text: str, orig: dict[str, str]) -> tuple[Patch, int]:
    lines = text.splitlines()  # preserves blank lines, no strip()
    if (
        len(lines) < 2
        or not Parser._norm(lines[0]).startswith('*** Begin Patch')
        or Parser._norm(lines[-1]) != '*** End Patch'
    ):
        raise DiffError('Invalid patch text - missing sentinels')

    parser = Parser(current_files=orig, lines=lines, index=1)
    parser.parse()
    return parser.patch, parser.fuzz


def identify_files_needed(text: str) -> list[str]:
    lines = text.splitlines()
    return [
        line[len('*** Update File: ') :]
        for line in lines
        if line.startswith('*** Update File: ')
    ] + [
        line[len('*** Delete File: ') :]
        for line in lines
        if line.startswith('*** Delete File: ')
    ]


def identify_files_added(text: str) -> list[str]:
    lines = text.splitlines()
    return [
        line[len('*** Add File: ') :]
        for line in lines
        if line.startswith('*** Add File: ')
    ]


# --------------------------------------------------------------------------- #
# File-system helpers
# --------------------------------------------------------------------------- #
def load_files(paths: list[str], open_fn: Callable[[str], str]) -> dict[str, str]:
    return {path: open_fn(path) for path in paths}


def apply_commit(
    commit: Commit,
    write_fn: Callable[[str, str], None],
    remove_fn: Callable[[str], None],
) -> None:
    for path, change in commit.changes.items():
        if change.type is ActionType.DELETE:
            remove_fn(path)
        elif change.type is ActionType.ADD:
            if change.new_content is None:
                raise DiffError(f'ADD change for {path} has no content')
            write_fn(path, change.new_content)
        elif change.type is ActionType.UPDATE:
            if change.new_content is None:
                raise DiffError(f'UPDATE change for {path} has no new content')
            target = change.move_path or path
            write_fn(target, change.new_content)
            if change.move_path:
                remove_fn(path)


def process_patch(
    text: str,
    open_fn: Callable[[str], str],
    write_fn: Callable[[str, str], None],
    remove_fn: Callable[[str], None],
) -> str:
    if not text.startswith('*** Begin Patch'):
        raise DiffError('Patch text must start with *** Begin Patch')
    paths = identify_files_needed(text)
    orig = load_files(paths, open_fn)
    patch, _fuzz = text_to_patch(text, orig)
    commit = patch_to_commit(patch, orig)
    apply_commit(commit, write_fn, remove_fn)
    return 'Done!'


# --------------------------------------------------------------------------- #
# Default FS helpers
# --------------------------------------------------------------------------- #
def open_file(path: str) -> str:
    with open(path, 'rt', encoding='utf-8') as fh:
        return fh.read()


def write_file(path: str, content: str) -> None:
    target = pathlib.Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('wt', encoding='utf-8') as fh:
        fh.write(content)


def remove_file(path: str) -> None:
    pathlib.Path(path).unlink(missing_ok=True)


# --------------------------------------------------------------------------- #
# CLI entry-point
# --------------------------------------------------------------------------- #
def main() -> None:
    import sys

    patch_text = sys.stdin.read()
    if not patch_text:
        print('Please pass patch text through stdin', file=sys.stderr)
        return
    try:
        result = process_patch(patch_text, open_file, write_file, remove_file)
    except DiffError as exc:
        print(exc, file=sys.stderr)
        return
    print(result)


if __name__ == '__main__':
    main()
