"""Utilities for loading microagents and converting them to Skills for V1 conversations.

This module provides functions to load microagents from various sources:
- Global microagents from OpenHands/microagents/
- User microagents from ~/.openhands/microagents/
- Repository-level microagents from the workspace

All microagents are converted to SDK Skill objects for use in V1 conversations.
"""

import logging
import os
from pathlib import Path

import openhands
from openhands.sdk.context.skills import Skill, load_user_skills
from openhands.sdk.workspace.remote.async_remote_workspace import AsyncRemoteWorkspace

_logger = logging.getLogger(__name__)

# Path to global microagents directory
GLOBAL_MICROAGENTS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(openhands.__file__)),
    'microagents',
)


def _find_global_microagent_files(microagent_dir: Path) -> list[Path]:
    """Find all .md files in the global microagents directory.

    Args:
        microagent_dir: Path to the global microagents directory

    Returns:
        List of Path objects to .md files (excluding README.md)
    """
    try:
        md_files = [
            f for f in microagent_dir.glob('*.md') if f.name.lower() != 'readme.md'
        ]
        return md_files
    except Exception as e:
        _logger.debug(f'Failed to find global microagent files: {str(e)}')
        return []


def _load_global_microagent_files(
    file_paths: list[Path], microagent_dir: Path
) -> list[Skill]:
    """Load skills from a list of global microagent files.

    Args:
        file_paths: List of file paths to load
        microagent_dir: Base microagents directory (for skill_dir parameter)

    Returns:
        List of Skill objects loaded from the files
    """
    skills = []

    for file_path in file_paths:
        try:
            skill = Skill.load(file_path, microagent_dir)
            skills.append(skill)
            _logger.debug(f'Loaded global microagent: {skill.name} from {file_path}')
        except Exception as e:
            _logger.warning(
                f'Failed to load global microagent from {file_path}: {str(e)}'
            )

    return skills


def load_global_microagents() -> list[Skill]:
    """Load global microagents from OpenHands/microagents/ directory.

    Returns:
        List of Skill objects loaded from global microagents directory.
        Returns empty list if directory doesn't exist or on errors.
    """
    microagent_dir = Path(GLOBAL_MICROAGENTS_DIR)

    # Check if directory exists
    if not microagent_dir.exists():
        _logger.debug(f'Global microagents directory does not exist: {microagent_dir}')
        return []

    try:
        _logger.info(f'Loading global microagents from {microagent_dir}')

        # Find all .md files in the directory
        md_files = _find_global_microagent_files(microagent_dir)

        # Load skills from the found files
        skills = _load_global_microagent_files(md_files, microagent_dir)

        _logger.info(
            f'Loaded {len(skills)} global microagents: {[s.name for s in skills]}'
        )

        return skills

    except Exception as e:
        _logger.warning(f'Failed to load global microagents: {str(e)}')
        return []


def load_user_microagents() -> list[Skill]:
    """Load user microagents from ~/.openhands/microagents/ directory.

    Uses the SDK's load_user_skills() function which handles loading from
    ~/.openhands/skills/ and ~/.openhands/microagents/ (for backward compatibility).

    Returns:
        List of Skill objects loaded from user directories.
        Returns empty list if no skills found or on errors.
    """
    try:
        skills = load_user_skills()
        _logger.info(
            f'Loaded {len(skills)} user microagents: {[s.name for s in skills]}'
        )
        return skills
    except Exception as e:
        _logger.warning(f'Failed to load user microagents: {str(e)}')
        return []


def _determine_repo_root(working_dir: str, selected_repository: str | None) -> str:
    """Determine the repository root directory.

    Args:
        working_dir: Base working directory path
        selected_repository: Repository name (e.g., 'owner/repo') or None

    Returns:
        Path to the repository root directory
    """
    if selected_repository:
        repo_name = selected_repository.split('/')[-1]
        return f'{working_dir}/{repo_name}'
    return working_dir


async def _read_file_from_workspace(
    workspace: AsyncRemoteWorkspace, file_path: str, working_dir: str
) -> str | None:
    """Read file content from remote workspace.

    Args:
        workspace: AsyncRemoteWorkspace to execute commands
        file_path: Path to the file to read
        working_dir: Working directory for command execution

    Returns:
        File content as string, or None if file doesn't exist or read fails
    """
    try:
        result = await workspace.execute_command(
            f'cat {file_path}', cwd=working_dir, timeout=10.0
        )
        if result.exit_code == 0 and result.stdout.strip():
            return result.stdout
        return None
    except Exception as e:
        _logger.debug(f'Failed to read file {file_path}: {str(e)}')
        return None


def _create_skill_from_content(filename: str, content: str) -> Skill | None:
    """Create a Skill object from file content.

    Args:
        filename: Name of the file (used for skill name derivation)
        content: File content to parse

    Returns:
        Skill object, or None if parsing fails
    """
    try:
        # Use simple string path to avoid Path filesystem operations
        skill = Skill.load(path=filename, skill_dir=None, file_content=content)
        return skill
    except Exception as e:
        _logger.warning(f'Failed to create skill from {filename}: {str(e)}')
        return None


async def _load_special_files(
    workspace: AsyncRemoteWorkspace, repo_root: str, working_dir: str
) -> list[Skill]:
    """Load special microagent files from repository root.

    Loads: .cursorrules, agents.md, agent.md

    Args:
        workspace: AsyncRemoteWorkspace to execute commands
        repo_root: Path to repository root directory
        working_dir: Working directory for command execution

    Returns:
        List of Skill objects loaded from special files
    """
    skills = []
    special_files = ['.cursorrules', 'agents.md', 'agent.md']

    for filename in special_files:
        file_path = f'{repo_root}/{filename}'
        content = await _read_file_from_workspace(workspace, file_path, working_dir)

        if content:
            skill = _create_skill_from_content(filename, content)
            if skill:
                skills.append(skill)
                _logger.debug(f'Loaded special file microagent: {skill.name}')

    return skills


async def _find_microagent_md_files(
    workspace: AsyncRemoteWorkspace, microagent_dir: str, working_dir: str
) -> list[str]:
    """Find all .md files in the microagents directory.

    Args:
        workspace: AsyncRemoteWorkspace to execute commands
        microagent_dir: Path to microagents directory
        working_dir: Working directory for command execution

    Returns:
        List of file paths to .md files (excluding README.md)
    """
    try:
        result = await workspace.execute_command(
            f"find {microagent_dir} -type f -name '*.md' 2>/dev/null || true",
            cwd=working_dir,
            timeout=10.0,
        )

        if result.exit_code == 0 and result.stdout.strip():
            file_paths = [
                f.strip()
                for f in result.stdout.strip().split('\n')
                if f.strip() and 'README.md' not in f
            ]
            return file_paths

        return []
    except Exception as e:
        _logger.debug(f'Failed to find microagent files in {microagent_dir}: {str(e)}')
        return []


async def _load_microagent_md_files(
    workspace: AsyncRemoteWorkspace,
    file_paths: list[str],
    microagent_dir: str,
    working_dir: str,
) -> list[Skill]:
    """Load skills from a list of microagent .md files.

    Args:
        workspace: AsyncRemoteWorkspace to execute commands
        file_paths: List of file paths to load
        microagent_dir: Base microagents directory (for calculating relative paths)
        working_dir: Working directory for command execution

    Returns:
        List of Skill objects loaded from the files
    """
    skills = []

    for file_path in file_paths:
        content = await _read_file_from_workspace(workspace, file_path, working_dir)

        if content:
            # Calculate relative path for skill name
            rel_path = file_path.replace(f'{microagent_dir}/', '')
            skill = _create_skill_from_content(rel_path, content)

            if skill:
                skills.append(skill)
                _logger.debug(f'Loaded repo microagent: {skill.name}')

    return skills


async def load_repo_microagents(
    workspace: AsyncRemoteWorkspace,
    selected_repository: str | None,
    working_dir: str,
) -> list[Skill]:
    """Load repository-level microagents from the workspace.

    Loads microagents from:
    1. Special files in repo root: .cursorrules, agents.md, agent.md
    2. .md files in .openhands/microagents/ directory

    Args:
        workspace: AsyncRemoteWorkspace to execute commands in the sandbox
        selected_repository: Repository name (e.g., 'owner/repo') or None
        working_dir: Working directory path

    Returns:
        List of Skill objects loaded from repository.
        Returns empty list on errors.
    """
    try:
        # Determine repository root directory
        repo_root = _determine_repo_root(working_dir, selected_repository)
        _logger.info(f'Loading repo microagents from {repo_root}')

        # Load special files from repo root
        special_skills = await _load_special_files(workspace, repo_root, working_dir)

        # Load .md files from .openhands/microagents/ directory
        microagent_dir = f'{repo_root}/.openhands/microagents'
        md_file_paths = await _find_microagent_md_files(
            workspace, microagent_dir, working_dir
        )
        md_skills = await _load_microagent_md_files(
            workspace, md_file_paths, microagent_dir, working_dir
        )

        # Combine all loaded skills
        all_skills = special_skills + md_skills

        _logger.info(
            f'Loaded {len(all_skills)} repo microagents: {[s.name for s in all_skills]}'
        )

        return all_skills

    except Exception as e:
        _logger.warning(f'Failed to load repo microagents: {str(e)}')
        return []


def merge_skills(skill_lists: list[list[Skill]]) -> list[Skill]:
    """Merge multiple skill lists, avoiding duplicates by name.

    Later lists take precedence over earlier lists for duplicate names.

    Args:
        skill_lists: List of skill lists to merge

    Returns:
        Deduplicated list of skills with later lists overriding earlier ones
    """
    skills_by_name = {}

    for skill_list in skill_lists:
        for skill in skill_list:
            if skill.name in skills_by_name:
                _logger.debug(
                    f'Overriding skill "{skill.name}" from earlier source with later source'
                )
            skills_by_name[skill.name] = skill

    result = list(skills_by_name.values())
    _logger.debug(f'Merged skills: {[s.name for s in result]}')
    return result
