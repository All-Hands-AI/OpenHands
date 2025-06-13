import json
import os

from litellm import completion

# set env

tools = [
    {
        'type': 'function',
        'function': {
            'name': 'execute_bash',
            'description': "Execute a bash command in the terminal within a persistent shell session.\n\n### Command Execution\n* One command at a time: You can only execute one bash command at a time. If you need to run multiple commands sequentially, use `&&` or `;` to chain them together.\n* Persistent session: Commands execute in a persistent shell session where environment variables, virtual environments, and working directory persist between commands.\n* Timeout: Commands have a soft timeout of 120 seconds, once that's reached, you have the option to continue or interrupt the command (see section below for details)\n\n### Running and Interacting with Processes\n* Long running commands: For commands that may run indefinitely, run them in the background and redirect output to a file, e.g. `python3 app.py > server.log 2>&1 &`.\n* Interact with running process: If a bash command returns exit code `-1`, this means the process is not yet finished. By setting `is_input` to `true`, you can:\n  - Send empty `command` to retrieve additional logs\n  - Send text (set `command` to the text) to STDIN of the running process\n  - Send control commands like `C-c` (Ctrl+C), `C-d` (Ctrl+D), or `C-z` (Ctrl+Z) to interrupt the process\n\n### Best Practices\n* Directory verification: Before creating new directories or files, first verify the parent directory exists and is the correct location.\n* Directory management: Try to maintain working directory by using absolute paths and avoiding excessive use of `cd`.\n\n### Output Handling\n* Output truncation: If the output exceeds a maximum length, it will be truncated before being returned.\n",
            'parameters': {
                'type': 'object',
                'properties': {
                    'command': {
                        'type': 'string',
                        'description': 'The bash command to execute. Can be empty string to view additional logs when previous exit code is `-1`. Can be `C-c` (Ctrl+C) to interrupt the currently running process. Note: You can only execute one bash command at a time. If you need to run multiple commands sequentially, you can use `&&` or `;` to chain them together.',
                    },
                    'is_input': {
                        'type': 'string',
                        'description': 'If True, the command is an input to the running process. If False, the command is a bash command to be executed in the terminal. Default is False.',
                        'enum': ['true', 'false'],
                    },
                },
                'required': ['command'],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'think',
            'description': 'Use the tool to think about something. It will not obtain new information or make any changes to the repository, but just log the thought. Use it when complex reasoning or brainstorming is needed.\n\nCommon use cases:\n1. When exploring a repository and discovering the source of a bug, call this tool to brainstorm several unique ways of fixing the bug, and assess which change(s) are likely to be simplest and most effective.\n2. After receiving test results, use this tool to brainstorm ways to fix failing tests.\n3. When planning a complex refactoring, use this tool to outline different approaches and their tradeoffs.\n4. When designing a new feature, use this tool to think through architecture decisions and implementation details.\n5. When debugging a complex issue, use this tool to organize your thoughts and hypotheses.\n\nThe tool simply logs your thought process for better transparency and does not execute any code or make changes.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'thought': {'type': 'string', 'description': 'The thought to log.'}
                },
                'required': ['thought'],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'finish',
            'description': "Signals the completion of the current task or conversation.\n\nUse this tool when:\n- You have successfully completed the user's requested task\n- You cannot proceed further due to technical limitations or missing information\n\nThe message should include:\n- A clear summary of actions taken and their results\n- Any next steps for the user\n- Explanation if you're unable to complete the task\n- Any follow-up questions if more information is needed\n\nThe task_completed field should be set to True if you believed you have completed the task, and False otherwise.\n",
            'parameters': {
                'type': 'object',
                'required': ['message', 'task_completed'],
                'properties': {
                    'message': {
                        'type': 'string',
                        'description': 'Final message to send to the user',
                    },
                    'task_completed': {
                        'type': 'string',
                        'enum': ['true', 'false', 'partial'],
                        'description': 'Whether you have completed the task.',
                    },
                },
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'str_replace_editor',
            'description': "Custom editing tool for viewing, creating and editing files in plain-text format\n* State is persistent across command calls and discussions with the user\n* If `path` is a file, `view` displays the result of applying `cat -n`. If `path` is a directory, `view` lists non-hidden files and directories up to 2 levels deep\n* The `create` command cannot be used if the specified `path` already exists as a file\n* If a `command` generates a long output, it will be truncated and marked with `<response clipped>`\n* The `undo_edit` command will revert the last edit made to the file at `path`\n\n\nBefore using this tool:\n1. Use the view tool to understand the file's contents and context\n2. Verify the directory path is correct (only applicable when creating new files):\n   - Use the view tool to verify the parent directory exists and is the correct location\n\nWhen making edits:\n   - Ensure the edit results in idiomatic, correct code\n   - Do not leave the code in a broken state\n   - Always use absolute file paths (starting with /)\n\nCRITICAL REQUIREMENTS FOR USING THIS TOOL:\n\n1. EXACT MATCHING: The `old_str` parameter must match EXACTLY one or more consecutive lines from the file, including all whitespace and indentation. The tool will fail if `old_str` matches multiple locations or doesn't match exactly with the file content.\n\n2. UNIQUENESS: The `old_str` must uniquely identify a single instance in the file:\n   - Include sufficient context before and after the change point (3-5 lines recommended)\n   - If not unique, the replacement will not be performed\n\n3. REPLACEMENT: The `new_str` parameter should contain the edited lines that replace the `old_str`. Both strings must be different.\n\nRemember: when making multiple file edits in a row to the same file, you should prefer to send all edits in a single message with multiple calls to this tool, rather than multiple messages with a single call each.\n",
            'parameters': {
                'type': 'object',
                'properties': {
                    'command': {
                        'description': 'The commands to run. Allowed options are: `view`, `create`, `str_replace`, `insert`, `undo_edit`.',
                        'enum': [
                            'view',
                            'create',
                            'str_replace',
                            'insert',
                            'undo_edit',
                        ],
                        'type': 'string',
                    },
                    'path': {
                        'description': 'Absolute path to file or directory, e.g. `/workspace/file.py`',
                        'type': 'string',
                    },
                    'file_text': {
                        'description': 'Required parameter of `create` command, with the content of the file to be created.',
                        'type': 'string',
                    },
                    'old_str': {
                        'description': 'Required parameter of `str_replace` command containing the string in `path` to replace.',
                        'type': 'string',
                    },
                    'new_str': {
                        'description': 'Optional parameter of `str_replace` command containing the new string (if not given, no string will be added). Required parameter of `insert` command containing the string to insert.',
                        'type': 'string',
                    },
                    'insert_line': {
                        'description': 'Required parameter of `insert` command. The `new_str` will be inserted AFTER the line `insert_line` of `path`.',
                        'type': 'integer',
                    },
                    'view_range': {
                        'description': 'Optional parameter of `view` command when `path` points to a file. If none is given, the full file is shown. If provided, the file will be shown in the indicated line number range, e.g. [11, 12] will show lines 11 and 12. Indexing at 1 to start. Setting `[start_line, -1]` shows all lines from `start_line` to the end of the file.',
                        'items': {'type': 'integer'},
                        'type': 'array',
                    },
                },
                'required': ['command', 'path'],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'get_webpage_content_and_summarize_mcp_tool_call',
            'description': '\n        This function fetch content from URL and summarize the content with corresponding goal.\n    Args:\n        url (URL): the target url to fetch content from (required)\n        goal (str): Extraction goal for the webpage (required)\n\n    Returns:\n        str: The returned response after summarization with goal\n    ',
            'parameters': {
                'type': 'object',
                'properties': {
                    'url': {'type': 'string', 'description': ''},
                    'goal': {'type': 'string', 'description': ''},
                },
                'required': ['url', 'goal'],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'search_web_content_based_on_keywords_mcp_tool_call',
            'description': 'Search the web and get SERP\n\n    Args:\n        keywords (str): The keyword to search on the web (required)\n        top_k (int): The number of top results to return\n\n    Returns:\n        str: The returned content\n    ',
            'parameters': {
                'type': 'object',
                'properties': {
                    'keywords': {'type': 'string', 'description': ''},
                    'top_k': {'type': 'string', 'description': ''},
                },
                'required': ['keywords'],
            },
        },
    },
]

messages = [
    {
        'content': [
            {
                'type': 'text',
                'text': "You are Thesis agent, an AI assistant that helps users answer questions and deliver clear, well-supported insights.\n- Use the knowledge base to reason and answer the question.\n- If you know the answer, respond directly.\n- If not, you just only use the available search tools to find authoritative information, not allow use another external tools.\n- Always analyze the query, plan your approach, execute the best next action, and conclude with a clear, structured answer.\n- Repeat the process (loop) if needed until the question is fully answered.\n\nDeliverables\n- Output Format: Final results (reports, code, summaries) are saved in .md format\n- File Naming: Include today's date (YYYY-MM-DD), e.g., analysis_2025-04-24.md\n- Date Stamp: Start each report with Date\n- Versioning: Archive prior versions (e.g., _v1, _2025-04-24T1530Z) in an /archive folder before updating\nIMPROTANT: Never show made-up links, made-up image or use deduction to made-up alt text in the markdown file. Only cite real URLs from the browser,.\nIMPORTANT: If user request to generate image, should recommend user to use deep research mode for advanced infor.\n\nUser sessions\n- User sessions are identified by a <session_id>.\n- Use user session id when needed when working with workspace in format /workspace/<session_id>\n\n\n<SEARCH_TOOL_INSTRUCTIONS>\nHere are the search tools you can use:\n\n- name: get_webpage_content_and_summarize_mcp_tool_call\n  description: \n        This function fetch content from URL and summarize the content with corresponding goal.\n    Args:\n        url (URL): the target url to fetch content from (required)\n        goal (str): Extraction goal for the webpage (required)\n\n    Returns:\n        str: The returned response after summarization with goal\n    \n\n- name: search_web_content_based_on_keywords_mcp_tool_call\n  description: Search the web and get SERP\n\n    Args:\n        keywords (str): The keyword to search on the web (required)\n        top_k (int): The number of top results to return\n\n    Returns:\n        str: The returned content\n    \ns\n</SEARCH_TOOL_INSTRUCTIONS>",
            }
        ],
        'role': 'system',
    },
    {
        'content': [
            {
                'type': 'text',
                'text': '<session_id>5f736f5d-2ea3-45d4-89a9-679cfde925c6</session_id>',
            },
            {
                'type': 'text',
                'text': "What's the ORAI balance of orai179dea42h80arp69zd779zcav5jp0kv04zx4h09",
            },
        ],
        'role': 'user',
    },
    {
        'content': [
            {
                'type': 'text',
                'text': "\n\n<RUNTIME_INFORMATION>\n\nThe user has access to the following hosts for accessing a web application,\neach of which has a corresponding port:\n* http://localhost:50943 (port 50943)\n* http://localhost:56017 (port 56017)\n\nWhen starting a web server, use the corresponding ports. You should also\nset any options to allow iframes and CORS requests, and allow the server to\nbe accessed from any host (e.g. 0.0.0.0).\nFor example, if you are using vite.config.js, you should set server.host and server.allowedHosts to true\n\n\n\nToday's date is 2025-06-11 (UTC).\n\n</RUNTIME_INFORMATION>",
                'cache_control': {'type': 'ephemeral'},
            }
        ],
        'role': 'user',
    },
    {
        'role': 'assistant',
        'content': [
            {
                'type': 'text',
                'text': 'Now let me search the web for the latest news about Oraichain.',
            }
        ],
        'tool_calls': [
            {
                'id': 'toolu_015pMSi5shNGELwebF3y4bLY',
                'type': 'function',
                'function': {
                    'name': 'search_web_content_based_on_keywords_mcp_tool_call',
                    'arguments': json.dumps({'keywords': 'Oraichain'}),
                },
            }
        ],
    },
    {
        'role': 'function',
        'name': 'search_web_content_based_on_keywords_mcp_tool_call',
        'content': '[1] Title: Oraichain (ORAI) Blockchain Explorer\n[1] URL Source: https://scan.orai.io/\n[1] Description: A search engine for data and service information within Oraichain network - AI Layer 1 for Data Economy and blockchain oracle Services.\n\n[2] Title: Oraichain (ORAI) Blockchain Explorer - ATOMScan\n[2] URL Source: https://atomscan.com/orai\n[2] Description: Blockchain explorer for Oraichain (ORAI), price information and transaction statistics.\n\n[3] Title: Cosmos Blockchain Explorer And Web Wallet - Scanium Dashboard\n[3] URL Source: https://scanium.io/Oraichain/gov/310\n[3] Description: Scanium Dashboard is a block explorer/web wallet for blockchains built on Cosmos SDK, Cosmoshub, Osmosis, Juno, Evmos, Injective, Canto and 70+ blockchains\n\n[4] Title: Mintscan: Interchain Explorer\n[4] URL Source: https://www.mintscan.io/\n[4] Description: Interchain block explorer and data analytics for sovereign blockchain networks.\n\n[5] Title: Oraichain price today, ORAI to USD live price, marketcap and chart\n[5] URL Source: https://coinmarketcap.com/currencies/oraichain-token\n[5] Description: The live Oraichain price today is $3.13 USD with a 24-hour trading volume of $821577.98 USD. We update our ORAI to USD price in real-time.\n',
    },
    # {
    #     'content': [
    #         {
    #             'type': 'text',
    #             'text': '[1] Title: Oraichain (ORAI) Blockchain Explorer\n[1] URL Source: https://scan.orai.io/\n[1] Description: A search engine for data and service information within Oraichain network - AI Layer 1 for Data Economy and blockchain oracle Services.\n\n[2] Title: Oraichain (ORAI) Blockchain Explorer - ATOMScan\n[2] URL Source: https://atomscan.com/orai\n[2] Description: Blockchain explorer for Oraichain (ORAI), price information and transaction statistics.\n\n[3] Title: Cosmos Blockchain Explorer And Web Wallet - Scanium Dashboard\n[3] URL Source: https://scanium.io/Oraichain/gov/310\n[3] Description: Scanium Dashboard is a block explorer/web wallet for blockchains built on Cosmos SDK, Cosmoshub, Osmosis, Juno, Evmos, Injective, Canto and 70+ blockchains\n\n[4] Title: Mintscan: Interchain Explorer\n[4] URL Source: https://www.mintscan.io/\n[4] Description: Interchain block explorer and data analytics for sovereign blockchain networks.\n\n[5] Title: Oraichain price today, ORAI to USD live price, marketcap and chart\n[5] URL Source: https://coinmarketcap.com/currencies/oraichain-token\n[5] Description: The live Oraichain price today is $3.13 USD with a 24-hour trading volume of $821577.98 USD. We update our ORAI to USD price in real-time.\n',
    #         }
    #     ],
    #     'role': 'tool',
    #     'tool_call_id': '',
    #     'name': 'search_web_content_based_on_keywords_mcp_tool_call',
    # },
    {
        'role': 'assistant',
        'content': [
            {
                'type': 'text',
                'text': 'Current date is 2025-06-11. Ignore anything that contradicts this.',
            }
        ],
    },
    {
        'role': 'user',
        'content': [
            {
                'type': 'text',
                'text': 'What is the capitol of Hanoi?',
            }
        ],
    },
]

response = completion(
    model='openai/models/gemini-2.5-pro-preview-05-06',
    messages=messages,
    tools=tools,
    tool_choice='auto',
    api_key=os.getenv('GEMINI_API_KEY'),
    base_url='https://generativelanguage.googleapis.com/v1beta/openai',
)

print(response)
print(response.usage)
