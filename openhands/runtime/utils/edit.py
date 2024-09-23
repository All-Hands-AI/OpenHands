import difflib
import os
import re
import tempfile
from abc import ABC, abstractmethod

from openhands.core.config import AppConfig
from openhands.core.logger import openhands_logger as logger
from openhands.events.action import (
    FileEditAction,
    FileReadAction,
    FileWriteAction,
)
from openhands.events.observation import (
    ErrorObservation,
    FileEditObservation,
    FileReadObservation,
    FileWriteObservation,
    Observation,
)
from openhands.llm.llm import LLM
from openhands.runtime.plugins.agent_skills.file_ops.file_ops import _lint_file

SYS_MSG = """Your job is to produce a new version of the file based on the old version and the
provided draft of the new version. The provided draft may be incomplete (it may skip lines) and/or incorrectly indented. You should try to apply the changes present in the draft to the old version, and output a new version of the file.
NOTE: The output file should be COMPLETE and CORRECTLY INDENTED. Do not omit any lines, and do not change any lines that are not part of the changes.
You should output the new version of the file by wrapping the new version of the file content in a ``` block.
"""
USER_MSG = """
HERE IS THE OLD VERSION OF THE FILE:
```
{old_contents}
```

HERE IS THE DRAFT OF THE NEW VERSION OF THE FILE:
```
{draft_changes}
```

"""


def _extract_code(string):
    pattern = r'```(?:\w*\n)?(.*?)```'
    matches = re.findall(pattern, string, re.DOTALL)
    if not matches:
        return None
    return matches[0].strip()


def get_new_file_contents(
    llm: LLM, old_contents: str, draft_changes: str, num_retries: int = 3
) -> str | None:
    while num_retries > 0:
        messages = [
            {'role': 'system', 'content': SYS_MSG},
            {
                'role': 'user',
                'content': USER_MSG.format(
                    old_contents=old_contents, draft_changes=draft_changes
                ),
            },
        ]
        print('messages for edit', messages)
        resp = llm.completion(messages=messages)
        print('raw response for edit', resp)
        new_contents = _extract_code(resp['choices'][0]['message']['content'])
        if new_contents is not None:
            return new_contents
        num_retries -= 1
    return None


def get_diff(old_contents: str, new_contents: str, filepath: str) -> str:
    diff = list(
        difflib.unified_diff(
            old_contents.strip().split('\n'),
            new_contents.strip().split('\n'),
            fromfile=filepath,
            tofile=filepath,
        )
    )
    return '\n'.join(map(lambda x: x.rstrip(), diff))


class FileEditRuntimeInterface(ABC):
    config: AppConfig

    @abstractmethod
    def read(self, action: FileReadAction) -> Observation:
        pass

    @abstractmethod
    def write(self, action: FileWriteAction) -> Observation:
        pass


class FileEditRuntimeMixin(FileEditRuntimeInterface):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        llm_config = self.config.get_llm_config()

        if llm_config.draft_editor is None:
            raise RuntimeError(
                'ERROR: Draft editor LLM is not set. Please set a draft editor LLM in the config.'
            )

        self.draft_editor_llm = LLM(llm_config.draft_editor)
        logger.info(
            f'[Draft edit functionality] enabled with LLM: {self.draft_editor_llm}'
        )

    def edit(self, action: FileEditAction) -> Observation:
        obs = self.read(FileReadAction(path=action.path))

        if (
            isinstance(obs, ErrorObservation)
            and 'File not found'.lower() in obs.content.lower()
        ):
            # directly write the new content
            obs = self.write(
                FileWriteAction(path=action.path, content=action.content.strip())
            )
            if isinstance(obs, ErrorObservation):
                return obs
            assert isinstance(obs, FileWriteObservation)
            return FileEditObservation(
                content=get_diff('', action.content, action.path),
                path=action.path,
                prev_exist=False,
            )
        elif isinstance(obs, FileReadObservation):
            old_file_content = obs.content
            updated_content = get_new_file_contents(
                self.draft_editor_llm, old_file_content, action.content
            )
            if updated_content is None:
                return ErrorObservation(
                    'Failed to get new file contents. '
                    'Please try to reduce the number of edits and try again.'
                )

            diff = get_diff(old_file_content, updated_content, action.path)

            # Lint the updated content
            if self.config.sandbox.enable_auto_lint:
                suffix = os.path.splitext(action.path)[1]
                with tempfile.NamedTemporaryFile(
                    suffix=suffix, mode='w+', encoding='utf-8'
                ) as temp_file:
                    temp_file.write(updated_content)
                    temp_file.flush()
                    lint_error, _ = _lint_file(temp_file.name)
                    if lint_error:
                        error_message = f'\n=== Linting failed for edited file [{action.path}] ===\n{lint_error}\n===\nChanges tried:\n{diff}\n==='
                        return ErrorObservation(error_message)

            obs = self.write(FileWriteAction(path=action.path, content=updated_content))
            return FileEditObservation(content=diff, path=action.path, prev_exist=True)
        else:
            logger.error(f'Unhandled error observation: {obs}')
            return obs
