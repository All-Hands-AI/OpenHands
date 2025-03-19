from typing import Optional

from  openhands.runtime.plugins.agent_skills.repo_ops.repo_index.chunk_index.codeblocks.parser.parser import CodeParser
from openhands.runtime.plugins.agent_skills.repo_ops.repo_index.chunk_index.codeblocks.parser.python import PythonParser


def is_supported(language: str) -> bool:
    return language in ['python', 'java', 'typescript', 'javascript']


def create_parser(language: str, **kwargs) -> Optional[CodeParser]:
    if language == 'python':
        return PythonParser(**kwargs)

    raise NotImplementedError(f'Language {language} is not supported.')
