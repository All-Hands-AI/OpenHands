import os
from dataclasses import dataclass, field

from opendevin.runtime.plugins.requirement import PluginRequirement
from opendevin.runtime.plugins.swe_agent_commands.parse_commands import (
    parse_command_file,
)


def _resolve_to_cur_dir(filename):
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)


def check_and_parse_command_file(filepath) -> str:
    if filepath is None:
        raise FileNotFoundError(f'File not found: {filepath}')
    return parse_command_file(filepath)


DEFAULT_SCRIPT_FILEPATHS = [
    _resolve_to_cur_dir('defaults.sh'),
    _resolve_to_cur_dir('search.sh'),
    _resolve_to_cur_dir('edit_linting.sh'),
]
DEFAULT_DOCUMENTATION = ''.join(
    [
        check_and_parse_command_file(filepath)
        for filepath in DEFAULT_SCRIPT_FILEPATHS
        if filepath is not None
    ]
)


@dataclass
class SWEAgentCommandsRequirement(PluginRequirement):
    name: str = 'swe_agent_commands'
    host_src: str = os.path.dirname(os.path.abspath(__file__))
    sandbox_dest: str = '/opendevin/plugins/swe_agent_commands'
    bash_script_path: str = 'setup_default.sh'

    scripts_filepaths: list[str | None] = field(
        default_factory=lambda: DEFAULT_SCRIPT_FILEPATHS
    )
    documentation: str = DEFAULT_DOCUMENTATION


CURSOR_SCRIPT_FILEPATHS = [
    _resolve_to_cur_dir('cursors_defaults.sh'),
    _resolve_to_cur_dir('cursors_edit_linting.sh'),
    _resolve_to_cur_dir('search.sh'),
]
CURSOR_DOCUMENTATION = ''.join(
    [
        check_and_parse_command_file(filepath)
        for filepath in CURSOR_SCRIPT_FILEPATHS
        if filepath is not None
    ]
)


@dataclass
class SWEAgentCursorCommandsRequirement(PluginRequirement):
    name: str = 'swe_agent_commands'
    host_src: str = os.path.dirname(os.path.abspath(__file__))
    sandbox_dest: str = '/opendevin/plugins/swe_agent_commands'
    bash_script_path: str = 'setup_cursor_mode.sh'

    scripts_filepaths: list[str | None] = field(
        default_factory=lambda: CURSOR_SCRIPT_FILEPATHS
    )
    documentation: str = CURSOR_DOCUMENTATION
