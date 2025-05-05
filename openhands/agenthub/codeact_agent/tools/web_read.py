from litellm import ChatCompletionToolParam, ChatCompletionToolParamFunctionChunk

_WEB_DESCRIPTION = """Read (convert to markdown) content from a webpage. You should prefer using the `web_read` tool over the `browser` tool, but do use the `browser` tool if you need to interact with a webpage (e.g., click a button, fill out a form, etc.) OR read a webpage that contains images.

You may use the `web_read` tool to read text content from a webpage, and even search the webpage content using a Google search query (e.g., url=`https://www.google.com/search?q=YOUR_QUERY`).

Only the most recently read webpage will be stored in memory. If you read a different webpage and want to refer to the previous one, you can use the `web_read` tool again with the previous URL. This means if you follow a link you will lose the content of the source page, so make a note of anything important before you move on.
"""

WebReadTool = ChatCompletionToolParam(
    type='function',
    function=ChatCompletionToolParamFunctionChunk(
        name='web_read',
        description=_WEB_DESCRIPTION,
        parameters={
            'type': 'object',
            'properties': {
                'url': {
                    'type': 'string',
                    'description': 'The URL of the webpage to read. You can also use a Google search query here (e.g., `https://www.google.com/search?q=YOUR_QUERY`).',
                }
            },
            'required': ['url'],
        },
    ),
)
