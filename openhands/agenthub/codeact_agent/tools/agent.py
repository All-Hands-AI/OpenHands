from litellm import ChatCompletionToolParam, ChatCompletionToolParamFunctionChunk

_AGENT_DESCRIPTION = """Launch a new agent that has access to read-only tools: {read_only_tools}. When you are searching for a keyword or file and are not confident that you will find the right match on the first try, use the Agent tool to perform the search for you. For example:

- If you are searching for a keyword like "config" or "logger", the Agent tool is appropriate
- If you want to read a specific file path, use the view or glob tool instead of the Agent tool, to find the match more quickly
- If you are searching for a specific class definition like "class Foo", use the glob tool instead, to find the match more quickly

NOTES:
1. When the agent is done, it will return a single message back to you. The result returned by the agent is not visible to the user. To show the user the result, you should send a text message back to the user with a concise summary of the result.
2. Each agent invocation is stateless. You will not be able to send additional messages to the agent, nor will the agent be able to communicate with you outside of its final report. Therefore, your prompt should contain a highly detailed task description for the agent to perform autonomously and you should specify exactly what information the agent should return back to you in its final and only message to you.
3. IMPORTANT: The agent can not use bash, file editor, or any other tools that modify files. If you want to use these tools, use them directly instead of going through the agent.`"""

AgentTool = ChatCompletionToolParam(
    type='function',
    function=ChatCompletionToolParamFunctionChunk(
        name='dispatch_agent',
        description=_AGENT_DESCRIPTION,
        parameters={
            'type': 'object',
            'properties': {
                'task': {
                    'type': 'string',
                    'description': 'The detailed task for the agent to perform.',
                },
            },
            'required': ['task'],
        },
    ),
)
