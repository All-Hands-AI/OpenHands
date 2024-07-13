import fnmatch
import json
import os
from typing import Any, List, Optional, Type

from pydantic import ValidationError

from opendevin.controller.agent import Agent
from opendevin.controller.state.state import State
from opendevin.core.logger import opendevin_logger as logger
from opendevin.events.action import Action, AgentFinishAction, MessageAction
from opendevin.llm.llm import LLM

from .file_context import RankedFileSpan
from .index.code_index import CodeIndex
from .index.settings import MoatlessIndexSettings
from .prompt import (
    FIND_AGENT_TEST_IGNORE,
    SEARCH_FUNCTIONS_FEW_SHOT,
    SEARCH_SYSTEM_PROMPT,
)
from .repository import FileRepository
from .search import (
    ActionCallWithContext,
    FindCodeResponse,
    IdentifyCode,
    IdentifyCodeRequest,
    SearchCodeAction,
)
from .settings import Settings
from .types import ActionSpec, FileWithSpans, Reject, RejectRequest
from .workspace import Workspace

SUPPORT_TEST_FILES: bool = False


def get_system_message() -> str:
    system_prompt = SEARCH_SYSTEM_PROMPT + SEARCH_FUNCTIONS_FEW_SHOT
    if not SUPPORT_TEST_FILES:
        system_prompt += FIND_AGENT_TEST_IGNORE
    return system_prompt


def action_to_str(action: Action) -> str:
    if isinstance(action, MessageAction):
        return action.content
    return ''


def get_action_message(action: Action) -> dict[str, str] | None:
    if isinstance(action, MessageAction):
        return {
            'role': 'user' if action.source == 'user' else 'assistant',
            'content': action_to_str(action),
        }
    return None


class MoatlessSearchAgent(Agent):
    VERSION = '2024-06-14'
    TOOLS: List[Type[ActionSpec]] = [SearchCodeAction, IdentifyCode, Reject]

    system_message: str = get_system_message()

    def __init__(self, llm: LLM):
        super().__init__(llm)

        self._tool_calls: list[ActionCallWithContext] = []
        self._is_retry: bool = False
        self._retry_messages: list[dict] = []
        self._previous_arguments: dict = {}

        Settings.agent_model = 'gpt-4o-2024-05-13'
        index_settings = MoatlessIndexSettings()

        repo_dir = '/Users/ryan/Developer/OpenDevin'
        file_repo = FileRepository(repo_dir)
        logger.info(f'📂 Loaded files from {repo_dir}')
        persist_dir = '.vector_store' + repo_dir
        # check if persist_dir exists
        if os.path.exists(persist_dir):
            code_index = CodeIndex.from_persist_dir(
                persist_dir=persist_dir, file_repo=file_repo
            )
        else:
            code_index = CodeIndex(file_repo=file_repo, settings=index_settings)
        nodes, tokens = code_index.run_ingestion()
        logger.info(f'🤓 Indexed {nodes} nodes and {tokens} tokens')
        code_index.persist(persist_dir=persist_dir)
        self._workspace = Workspace(file_repo=file_repo, code_index=code_index)
        self._identified_or_rejected = False
        self._finish_content = ''

    def step(self, state: State) -> Action:
        """
        Perform one search step using the agent.
        """
        if self._identified_or_rejected:
            return AgentFinishAction(outputs={'content': self._finish_content})

        messages: list[dict[str, str]] = [
            {'role': 'system', 'content': self.system_message},
        ]

        if (task_message := state.get_current_user_intent()) is None:
            task_message = state.inputs['task']
        messages.append({'role': 'user', 'content': task_message})

        for tool_call in self._tool_calls:
            arguments_json = (
                json.dumps(tool_call.arguments) if tool_call.arguments else '{}'
            )
            messages.append(
                {
                    'role': 'assistant',
                    'tool_calls': (  # type: ignore
                        [
                            {
                                'id': tool_call.call_id,
                                'type': 'function',
                                'function': {
                                    'name': tool_call.action_name,
                                    'arguments': arguments_json,
                                },
                            }
                        ]
                    ),
                }
            )

            content = tool_call.message or ''
            if tool_call.file_context:
                content += '\n\n'
                content += tool_call.file_context.create_prompt(
                    show_span_ids=True,
                    show_line_numbers=False,
                    exclude_comments=True,
                    show_outcommented_code=True,
                    outcomment_code_comment='... rest of the code',
                )
                logger.info(f'🔍 file context dict: {tool_call.file_context.dict()}')
            else:
                logger.info(
                    f'😥 \n\nNo file context available for this tool call {tool_call.call_id}.'
                )

            messages.append(
                {
                    'tool_call_id': tool_call.call_id,
                    'role': 'tool',
                    'name': tool_call.action_name,
                    'content': content,
                }
            )

        messages += self._retry_messages  # FIXME: check if _retry_messages is correct
        logger.info(f'👀 Messages: {messages}')

        response = self.llm._completion(
            messages=messages,
            max_tokens=1000,
            stop=[],
            tools=self._tool_specs(),
            temperature=0.0,
        )
        response_message = response.choices[0].message

        if hasattr(response_message, 'tool_calls'):
            for tool_call in response_message.tool_calls:
                try:
                    arguments = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    logger.warning(
                        f'Failed to parse arguments: {tool_call.function.arguments}'
                    )
                    return self._retry(
                        response_message,
                        f'Failed to parse arguments: {tool_call.function.arguments}. Make sure the function is called properly.',
                        tool_call=tool_call,
                    )

                function_name = tool_call.function.name
                if function_name == IdentifyCode.name():
                    response, file_context = self._identify(tool_call.id, arguments)
                    if response:
                        self._identified_or_rejected = True
                        self._finish_content = (
                            response.message + '\n' + file_context.create_prompt()
                        )
                        return MessageAction(content=self._finish_content)
                elif function_name == Reject.name():
                    reject_request = RejectRequest.model_validate(arguments)
                    self._identified_or_rejected = True
                    self._finish_content = reject_request.reason
                    return MessageAction(content=self._finish_content)
                elif function_name == SearchCodeAction.name():
                    ranked_spans = []
                    try:
                        if self._previous_arguments == arguments:
                            logger.warning(
                                f'Got same arguments as last call: {arguments}..'
                            )
                            if self._is_retry:
                                raise Exception(
                                    f'Got same arguments as last call to {function_name} and {arguments}.'
                                )
                            message = 'The search arguments are the same as the previous call. You must use different arguments to continue.'
                        else:
                            self._previous_arguments = arguments

                            search_action = SearchCodeAction(self._workspace.code_index)
                            search_request = search_action.validate_request(arguments)

                            if (
                                not SUPPORT_TEST_FILES
                                and search_request.file_pattern
                                and is_test_pattern(search_request.file_pattern)
                            ):
                                message = "It's not possible to search for test files."
                            else:
                                search_result = search_action.search(search_request)

                                for hit in search_result.hits:
                                    for span in hit.spans:
                                        ranked_spans.append(
                                            RankedFileSpan(
                                                file_path=hit.file_path,
                                                span_id=span.span_id,
                                                rank=span.rank,
                                            )
                                        )
                                message = search_result.message or ''
                    except ValidationError as e:
                        logger.warning(f'Failed to validate function call. Error: {e}')
                        message = f'The function call is invalid. Error: {e}'

                        if self._is_retry:
                            raise e

                        self._is_retry = True
                    except Exception as e:
                        raise e

                    self._add_to_message_history(
                        tool_call.id,
                        function_name,
                        arguments,
                        ranked_spans,
                        message,
                    )
                    return MessageAction(content=message)
                else:
                    logger.warning(f'Unknown function used: {function_name}')
                    return self._retry(
                        response_message,
                        f'Unknown function: {function_name}',
                        tool_call=tool_call,
                    )

                self._is_retry = False

        elif self._is_retry:
            logger.warning('The LLM retried without a tool call, aborting')
            raise Exception('The LLM retried without a tool call, aborting')
        elif self._tool_calls:
            return self._retry(
                response_message,
                "I expected a function call in the response. If you're done, please use the identify function.",
            )

        return self._retry(
            response_message, 'I expected a function call in the response.'
        )

    def reset(self) -> None:
        """
        Resets the Agent.
        """
        return super().reset()

    def _tool_specs(self) -> list[dict[str, Any]]:
        return [tool.openai_tool_spec() for tool in self.TOOLS]

    def _identify(self, tool_call_id: str, arguments: dict[str, Any]):
        identify_request = IdentifyCodeRequest.model_validate(arguments)

        files_with_missing_spans = self._find_missing_spans(
            identify_request.files_with_spans
        )
        if files_with_missing_spans:
            message = 'identify() The following span ids are not in the file context: '

            for file_with_spans in files_with_missing_spans:
                message += f"\n{file_with_spans.file_path}: {', '.join(file_with_spans.span_ids)}"

            logger.warning(message)

            # self._add_to_message_history(
            #    tool_call_id, "identify", arguments, [], message
            # )

            # return None

        file_context = self._workspace.create_file_context()
        for file_with_spans in identify_request.files_with_spans:
            file_context.add_spans_to_context(
                file_with_spans.file_path,
                file_with_spans.span_ids,
            )

        logger.info(
            f'find_code: Found {len(file_context.files)} files and {file_context.context_size()}.'
        )

        # self._expand_context_with_related_spans(file_context)

        response = FindCodeResponse(
            message=identify_request.reasoning, files=file_context.to_files_with_spans()
        )

        return response, file_context

    def _find_missing_spans(self, files_with_spans: list[FileWithSpans]):
        files_with_missing_spans = []
        for file_with_spans in files_with_spans:
            missing_spans = []
            for span_id in file_with_spans.span_ids:
                if not self._span_is_in_context(file_with_spans.file_path, span_id):
                    missing_spans.append(span_id)

            if missing_spans:
                files_with_missing_spans.append(
                    FileWithSpans(
                        file_path=file_with_spans.file_path, span_ids=missing_spans
                    )
                )

        return files_with_missing_spans

    def _span_is_in_context(self, file_path: str, span_id: str) -> bool:
        for previous_call in self._tool_calls:
            if previous_call.file_context.has_span(file_path, span_id):
                return True

        return False

    def _add_to_message_history(
        self,
        call_id: str,
        action_name: str,
        arguments: dict,
        ranked_spans: List[RankedFileSpan],
        message: Optional[str] = None,
    ):
        file_context = self._workspace.create_file_context()
        file_context.add_ranked_spans(ranked_spans)

        for previous_call in self._tool_calls:
            for span in ranked_spans:
                previous_call.file_context.remove_span_from_context(
                    span.file_path, span.span_id, remove_file=True
                )

        self._tool_calls.append(
            ActionCallWithContext(
                call_id=call_id,
                action_name=action_name,
                arguments=arguments,
                file_context=file_context,
                message=message,
            )
        )

    def _retry(
        self,
        response_message,
        message: str,
        tool_call: Optional[Any] = None,
    ):
        self._retry_messages.append(response_message.dict())

        if tool_call:
            self._retry_messages.append(
                {
                    'tool_call_id': tool_call.id,
                    'role': 'tool',
                    'name': tool_call.function.name,
                    'content': message,
                }
            )
        else:
            self._retry_messages.append(
                {
                    'role': 'user',
                    'content': message,
                }
            )
        self._is_retry = True

        return MessageAction(content=message)

    def search_memory(self, query: str) -> list[str]:
        raise NotImplementedError('Implement this abstract method')


def is_test_pattern(file_pattern: str):
    test_patterns = ['test_*.py', '/tests/']
    for pattern in test_patterns:
        if pattern in file_pattern:
            return True

    if file_pattern.startswith('test'):
        return True

    test_patterns = ['test_*.py']

    for pattern in test_patterns:
        if fnmatch.filter([file_pattern], pattern):
            return True

    return False
