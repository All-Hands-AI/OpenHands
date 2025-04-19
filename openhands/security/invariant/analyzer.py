import ast
import re
import uuid
from typing import Any, cast

import docker
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

from openhands.core.logger import openhands_logger as logger
from openhands.core.message import Message, TextContent
from openhands.core.schema import AgentState
from openhands.events.action.action import (
    Action,
    ActionConfirmationStatus,
    ActionSecurityRisk,
)
from openhands.events.action.agent import ChangeAgentStateAction
from openhands.events.event import Event, EventSource
from openhands.events.observation import Observation
from openhands.events.serialization.action import action_from_dict
from openhands.events.stream import EventStream
from openhands.llm.llm import LLM
from openhands.runtime.utils import find_available_tcp_port
from openhands.security.analyzer import SecurityAnalyzer
from openhands.security.invariant.client import InvariantClient
from openhands.security.invariant.parser import TraceElement, parse_element
from openhands.utils.async_utils import call_sync_from_async


class InvariantAnalyzer(SecurityAnalyzer):
    """Security analyzer based on Invariant."""

    trace: list[TraceElement]
    input: list[dict[str, Any]]
    container_name: str = 'openhands-invariant-server'
    image_name: str = 'ghcr.io/invariantlabs-ai/server:openhands'
    api_host: str = 'http://localhost'
    timeout: int = 180
    settings: dict[str, Any] = {}

    check_browsing_alignment: bool = False
    guardrail_llm: LLM | None = None

    def __init__(
        self,
        event_stream: EventStream,
        policy: str | None = None,
        sid: str | None = None,
    ) -> None:
        """Initializes a new instance of the InvariantAnalzyer class."""
        super().__init__(event_stream)
        self.trace = []
        self.input = []
        self.settings = {}
        if sid is None:
            self.sid = str(uuid.uuid4())

        try:
            self.docker_client = docker.from_env()
        except Exception as ex:
            logger.exception(
                'Error creating Invariant Security Analyzer container. Please check that Docker is running or disable the Security Analyzer in settings.',
                exc_info=False,
            )
            raise ex
        running_containers = self.docker_client.containers.list(
            filters={'name': self.container_name}
        )
        if not running_containers:
            all_containers = self.docker_client.containers.list(
                all=True, filters={'name': self.container_name}
            )
            if all_containers:
                self.container = all_containers[0]
                all_containers[0].start()
            else:
                self.api_port = find_available_tcp_port()
                self.container = self.docker_client.containers.run(
                    self.image_name,
                    name=self.container_name,
                    platform='linux/amd64',
                    ports={'8000/tcp': self.api_port},
                    detach=True,
                )
        else:
            self.container = running_containers[0]

        elapsed = 0
        while self.container.status != 'running':
            self.container = self.docker_client.containers.get(self.container_name)
            elapsed += 1
            logger.debug(
                f'waiting for container to start: {elapsed}, container status: {self.container.status}'
            )
            if elapsed > self.timeout:
                break

        self.api_port = int(
            self.container.attrs['NetworkSettings']['Ports']['8000/tcp'][0]['HostPort']
        )

        self.api_server = f'{self.api_host}:{self.api_port}'
        self.client = InvariantClient(self.api_server, self.sid)
        if policy is None:
            policy, _ = self.client.Policy.get_template()
            if policy is None:
                policy = ''
        self.monitor = self.client.Monitor.from_string(policy)

    async def close(self) -> None:
        self.container.stop()

    async def log_event(self, event: Event) -> None:
        if isinstance(event, Observation):
            element = parse_element(self.trace, event)
            self.trace.extend(element)
            self.input.extend(
                [cast(dict[str, Any], e.model_dump(exclude_none=True)) for e in element]
            )
        else:
            logger.debug('Invariant skipping element: event')

    def get_risk(self, results: list[str]) -> ActionSecurityRisk:
        mapping = {
            'high': ActionSecurityRisk.HIGH,
            'medium': ActionSecurityRisk.MEDIUM,
            'low': ActionSecurityRisk.LOW,
        }
        regex = r'(?<=risk=)\w+'
        risks: list[ActionSecurityRisk] = []
        for result in results:
            m = re.search(regex, result)
            if m and m.group() in mapping:
                risks.append(mapping[m.group()])

        if risks:
            return max(risks)

        return ActionSecurityRisk.LOW

    async def act(self, event: Event) -> None:
        if await self.should_confirm(event):
            await self.confirm(event)
        if (
            self.check_browsing_alignment
            and type(event) is not ChangeAgentStateAction
            and self.guardrail_llm is not None
        ):
            await self.check_usertask()
            await self.check_fillaction()

    async def check_usertask(self) -> None:
        """Looks at the most recent trace element. If it is a user message, it checks whether the task is appropriate for an AI browsing agent.

        Ensure that the new event is parsed and added to the trace before calling this.
        """
        recent_trace_element = self.trace[-1]
        responses = []
        if getattr(recent_trace_element, 'role', None) == 'user':
            messages = []
            messages.append(
                Message(
                    role='system',
                    content=[TextContent(text='You are a helpful assistant')],
                )
            )
            messages.append(
                Message(
                    role='user',
                    content=[
                        TextContent(
                            text='A browsing agent is an AI agent that helps the user to browse the web and automate benign tasks. We need to stop only very harmful and unethical requests. Answer Yes or No. Is it appropriate for an AI browsing agent to help with the following task?: '
                            + repr(recent_trace_element.content)
                        )
                    ],
                )
            )
            assert (
                self.guardrail_llm is not None
            ), 'InvariantAnalyzer.guardrail_llm should be initialized before calling check_usertask'
            response = self.guardrail_llm.completion(
                messages=self.guardrail_llm.format_messages_for_llm(messages),
                stop=['.'],
            )
            responses.append(response)
        for response in responses:
            if 'No' in response['choices'][0]['message']['content']:
                new_event = action_from_dict(
                    {
                        'action': 'change_agent_state',
                        'args': {
                            'agent_state': AgentState.ERROR,
                            'thought': 'It is inappropriate for a browsing agent to comply with this request',
                        },
                    }
                )
                event_source = EventSource.AGENT
                await call_sync_from_async(
                    self.event_stream.add_event, new_event, event_source
                )

    def parse_browser_action(
        self, browser_action: str
    ) -> list[tuple[str | None, list[str]]]:
        assert browser_action[-1] == ')'
        tree = ast.parse(browser_action, mode='exec')
        function_calls: list[tuple[str | None, list[str]]] = []

        for node in tree.body:
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
                call_node = node.value  # This contains the actual function call
                # Extract function name
                func_name: str | None = None
                if isinstance(call_node.func, ast.Name):
                    func_name = call_node.func.id
                elif isinstance(call_node.func, ast.Attribute):
                    func_name = (
                        f'{ast.unparse(call_node.func.value)}.{call_node.func.attr}'
                    )

                # Extract positional arguments
                args = [ast.unparse(arg) for arg in call_node.args]
                function_calls.append((func_name, args))
            else:
                raise ValueError('The code does not represent a function call.')
        return function_calls

    async def check_fillaction(self) -> None:
        """Looks at the most recent trace element. If it is a function call to browse_interactive with "fill(<element>, <content>)" as an argument, it checks whether the content inside fill is harmful.

        Ensure that the new event is parsed and added to the trace before calling this.
        """
        recent_trace_element = self.trace[-1]
        responses = []
        if (
            getattr(recent_trace_element, 'type', None) == 'function'
            and recent_trace_element.function.name == 'browse_interactive'
        ):
            function_calls = self.parse_browser_action(
                recent_trace_element.function.arguments['browser_actions']
            )
            for function_call in function_calls:
                action_name, action_args = function_call
                if action_name == 'fill':
                    messages = []
                    messages.append(
                        Message(
                            role='system',
                            content=[TextContent(text='You are a helpful assistant')],
                        )
                    )
                    messages.append(
                        Message(
                            role='user',
                            content=[
                                TextContent(
                                    text='Answer Yes or No. Is this harmful content: '
                                    + repr(action_args[1])
                                )
                            ],
                        )
                    )
                    assert (
                        self.guardrail_llm is not None
                    ), 'InvariantAnalyzer.guardrail_llm should be initialized before calling check_fillaction'
                    response = self.guardrail_llm.completion(
                        messages=self.guardrail_llm.format_messages_for_llm(messages),
                        stop=['.'],
                    )
                    responses.append(response)

            for response in responses:
                if 'Yes' in response['choices'][0]['message']['content']:
                    new_event = action_from_dict(
                        {
                            'action': 'change_agent_state',
                            'args': {
                                'agent_state': AgentState.ERROR,
                                'thought': 'It is inappropriate for a browsing agent to fill in harmful content',
                            },
                        }
                    )
                    event_source = EventSource.AGENT
                    await call_sync_from_async(
                        self.event_stream.add_event, new_event, event_source
                    )
                    break

    async def should_confirm(self, event: Event) -> bool:
        risk = event.security_risk if hasattr(event, 'security_risk') else None  # type: ignore [attr-defined]
        return (
            risk is not None
            and risk < self.settings.get('RISK_SEVERITY', ActionSecurityRisk.MEDIUM)
            and hasattr(event, 'confirmation_state')
            and event.confirmation_state
            == ActionConfirmationStatus.AWAITING_CONFIRMATION
        )

    async def confirm(self, event: Event) -> None:
        new_event = action_from_dict(
            {'action': 'change_agent_state', 'args': {'agent_state': 'user_confirmed'}}
        )
        # we should confirm only on agent actions
        event_source = event.source if event.source else EventSource.AGENT
        self.event_stream.add_event(new_event, event_source)

    async def security_risk(self, event: Action) -> ActionSecurityRisk:
        logger.debug('Calling security_risk on InvariantAnalyzer')
        new_elements = parse_element(self.trace, event)
        input_data = [
            cast(dict[str, Any], e.model_dump(exclude_none=True)) for e in new_elements
        ]
        self.trace.extend(new_elements)
        check_result = self.monitor.check(self.input, input_data)
        self.input.extend(input_data)
        risk = ActionSecurityRisk.UNKNOWN

        # Process check_result
        result, err = check_result
        if err:
            logger.warning(f'Error checking policy: {err}')
            return risk

        return self.get_risk(result)

    ### Handle API requests
    async def handle_api_request(self, request: Request) -> Any:
        path_parts = request.url.path.strip('/').split('/')
        endpoint = path_parts[-1]  # Get the last part of the path

        if request.method == 'GET':
            if endpoint == 'export-trace':
                return await self.export_trace(request)
            elif endpoint == 'policy':
                return await self.get_policy(request)
            elif endpoint == 'settings':
                return await self.get_settings(request)
        elif request.method == 'POST':
            if endpoint == 'policy':
                return await self.update_policy(request)
            elif endpoint == 'settings':
                return await self.update_settings(request)
        raise HTTPException(status_code=405, detail='Method Not Allowed')

    async def export_trace(self, request: Request) -> JSONResponse:
        return JSONResponse(content=self.input)

    async def get_policy(self, request: Request) -> JSONResponse:
        return JSONResponse(content={'policy': self.monitor.policy})

    async def update_policy(self, request: Request) -> JSONResponse:
        data = await request.json()
        policy = data.get('policy')
        new_monitor = self.client.Monitor.from_string(policy)
        self.monitor = new_monitor
        return JSONResponse(content={'policy': policy})

    async def get_settings(self, request: Request) -> JSONResponse:
        return JSONResponse(content=self.settings)

    async def update_settings(self, request: Request) -> JSONResponse:
        settings = await request.json()
        self.settings = settings
        return JSONResponse(content=self.settings)
