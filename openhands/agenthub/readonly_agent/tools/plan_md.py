from litellm import ChatCompletionToolParam, ChatCompletionToolParamFunctionChunk

PLAN_MD_TOOL_NAME = 'plan_md'

_PLAN_MD_DESCRIPTION = """Maintain the planning document PLAN.md in the repository root.

This tool is ONLY for planning. It can:
- view: Show the current contents of PLAN.md
- create: Create PLAN.md with provided text (fails if file already exists)
- edit: Replace PLAN.md content with provided text

It MUST NOT be used to modify any other file.
"""


def create_plan_md_tool() -> ChatCompletionToolParam:
    return ChatCompletionToolParam(
        type='function',
        function=ChatCompletionToolParamFunctionChunk(
            name=PLAN_MD_TOOL_NAME,
            description=_PLAN_MD_DESCRIPTION,
            parameters={
                'type': 'object',
                'properties': {
                    'command': {
                        'type': 'string',
                        'enum': ['view', 'create', 'edit'],
                        'description': 'Operation to perform on PLAN.md',
                    },
                    'file_text': {
                        'type': 'string',
                        'description': 'Required for create: Initial content of PLAN.md',
                    },
                    'old_str': {
                        'type': 'string',
                        'description': 'Required for edit: EXACT current content of PLAN.md (unique match). Use plan_md.view first.',
                    },
                    'new_str': {
                        'type': 'string',
                        'description': 'Required for edit: New full content of PLAN.md (replaces file)',
                    },
                },
                'required': ['command'],
                'additionalProperties': False,
            },
        ),
    )
