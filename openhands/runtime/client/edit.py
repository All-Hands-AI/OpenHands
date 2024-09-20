import difflib
import re

from openhands.llm.llm import LLM

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
    assert matches
    return matches[0].strip()


def get_new_file_contents(llm: LLM, old_contents: str, draft_changes: str) -> str:
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
    return _extract_code(resp['choices'][0]['message']['content'])


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
