from typing import Optional, Union

from invariant.stdlib.invariant.nodes import Function, Message, ToolCall, ToolOutput
from pydantic import BaseModel, Field

from opendevin.core.logger import opendevin_logger as logger
from opendevin.events.action import (
    Action,
    AgentDelegateAction,
    AgentFinishAction,
    BrowseInteractiveAction,
    BrowseURLAction,
    ChangeAgentStateAction,
    CmdKillAction,
    CmdRunAction,
    IPythonRunCellAction,
    MessageAction,
    NullAction,
)
from opendevin.events.event import EventSource
from opendevin.events.observation import (
    AgentDelegateObservation,
    AgentStateChangedObservation,
    BrowserOutputObservation,
    CmdOutputObservation,
    IPythonRunCellObservation,
    NullObservation,
    Observation,
)

TraceElement = Union[Message, ToolCall, ToolOutput, Function]


def get_next_id(trace: TraceElement) -> str:
    used_ids = [el.id for el in trace if type(el) == ToolCall]
    for i in range(1, len(used_ids) + 2):
        if str(i) not in used_ids:
            return str(i)
    return '1'


def get_last_id(
    trace: list[TraceElement],
) -> Optional[str]:
    for el in reversed(trace):
        if type(el) == ToolCall:
            return el.id
    return None


def parse_action(trace: list, action: Action) -> list[TraceElement]:
    next_id = get_next_id(trace)
    inv_trace = []  # type: list[TraceElement]
    if type(action) == MessageAction:
        if action.source == EventSource.USER:
            inv_trace.append(Message(role='user', content=action.content))
        else:
            inv_trace.append(Message(role='assistant', content=action.content))
    elif type(action) == IPythonRunCellAction:
        function = Function(
            name='ipython_run_cell',
            arguments={
                'code': action.code,
                'kernel_init_code': action.kernel_init_code,
            },
        )
        inv_trace.append(Message(role='assistant', content=action.thought))
        inv_trace.append(ToolCall(id=next_id, type='function', function=function))
        # inv_trace.append({"role": "assistant", "content": action.thought, "tool_calls": [tool_call]})
    elif type(action) == AgentFinishAction:
        function = Function(name='agent_finish', arguments={'outputs': action.outputs})
        inv_trace.append(Message(role='assistant', content=action.thought))
        inv_trace.append(ToolCall(id=next_id, type='function', function=function))
        # inv_trace.append({"role": "assistant", "content": action.thought, "tool_calls": [tool_call]})
    elif type(action) == CmdRunAction:
        function = Function(
            name='cmd_run',
            arguments={'command': action.command, 'background': action.background},
        )
        inv_trace.append(Message(role='assistant', content=action.thought))
        inv_trace.append(ToolCall(id=next_id, type='function', function=function))
    elif type(action) == CmdKillAction:
        function = Function(
            name='cmd_kill', arguments={'command_id': action.command_id}
        )
        inv_trace.append(Message(role='assistant', content=action.thought))
        inv_trace.append(ToolCall(id=next_id, type='function', function=function))
    elif type(action) == AgentDelegateAction:
        function = Function(
            name='agent_delegate',
            arguments={'agent': action.agent, 'inputs': action.inputs},
        )
        inv_trace.append(Message(role='assistant', content=action.thought))
        inv_trace.append(ToolCall(id=next_id, type='function', function=function))
    elif type(action) == BrowseInteractiveAction:
        function = Function(
            name='browse_interactive',
            arguments={
                'browser_actions': action.browser_actions,
                'browsergym_send_msg_to_user': action.browsergym_send_msg_to_user,
            },
        )
        inv_trace.append(Message(role='assistant', content=action.thought))
        inv_trace.append(ToolCall(id=next_id, type='function', function=function))
    elif type(action) == BrowseURLAction:
        function = Function(name='browse_url', arguments={'url': action.url})
        inv_trace.append(Message(role='assistant', content=action.thought))
        inv_trace.append(ToolCall(id=next_id, type='function', function=function))
    elif type(action) in [NullAction, ChangeAgentStateAction]:
        pass
    else:
        logger.error(f'Unknown action type: {type(action)}')
    return inv_trace


def parse_observation(trace: list[dict], obs: Observation) -> list[TraceElement]:
    last_id = get_last_id(trace)
    if type(obs) == NullObservation:
        return []
    elif type(obs) == CmdOutputObservation:
        return [ToolOutput(role='tool', content=obs.content, tool_call_id=last_id)]
    elif type(obs) == IPythonRunCellObservation:
        return [ToolOutput(role='tool', content=obs.content, tool_call_id=last_id)]
    elif type(obs) == AgentStateChangedObservation:
        return []
    elif type(obs) == BrowserOutputObservation:
        return [ToolOutput(role='tool', content=obs.content, tool_call_id=last_id)]
    elif type(obs) == AgentDelegateObservation:
        return [ToolOutput(role='tool', content=obs.content, tool_call_id=last_id)]
    logger.error(f'Unknown observation type: {type(obs)}')
    return []


def parse_element(trace: list[dict], element: Action | Observation) -> list[dict]:
    if isinstance(element, Action):
        return parse_action(trace, element)
    return parse_observation(trace, element)


def print_inv_trace(trace: list[dict]):
    for element in trace:
        print(element)


def parse_trace(trace: list[tuple[Action, Observation]]):
    inv_trace = []  # type: list[TraceElement]
    for action, obs in trace:
        inv_trace.extend(parse_action(inv_trace, action))
        inv_trace.extend(parse_observation(inv_trace, obs))
    return inv_trace


class InvariantState(BaseModel):
    trace: list[dict] = Field(default_factory=list)

    def add_action(self, action: Action):
        self.trace.extend(parse_action(self.trace, action))

    def add_observation(self, obs: Observation):
        self.trace.extend(parse_observation(self.trace, obs))

    def concatenate(self, other: 'InvariantState'):
        self.trace.extend(other.trace)
