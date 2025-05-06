from litellm import ChatCompletionToolParam, ChatCompletionToolParamFunctionChunk


_CREATE_PR_DESCRIPTION = """Use the tool to open a pull request for GitHub or GitLab.
You should not use the GitHub or GitLab API to open a pull request, and use this tool instead.
"""


CreatePRTool = ChatCompletionToolParam(
    type='function',
    function=ChatCompletionToolParamFunctionChunk(
        name='create_pr',
        description=_CREATE_PR_DESCRIPTION,
        parameters={
            'type': 'object',
            'properties': {
                'source_branch': {'type': 'string', 'description': 'branch containing new modifications'},
                'target_branch': {'type': 'string', 'description': 'branch you request to merge your changes into'}
            },
            'required': ['source_branch', 'target_branch']
        }
    )
)