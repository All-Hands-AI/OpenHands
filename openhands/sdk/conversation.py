from __future__ import annotations

import json
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable

from openhands.core.config import OpenHandsConfig
from openhands.events.action import CmdRunAction, FileReadAction, FileWriteAction
from openhands.events.observation import (
    CmdOutputObservation,
    ErrorObservation,
    FileReadObservation,
    FileWriteObservation,
)
from openhands.events.stream import EventStream, EventStreamSubscriber
from openhands.llm.llm_registry import LLMRegistry
from openhands.runtime.base import Runtime
from openhands.runtime.impl.cli.cli_runtime import CLIRuntime
from openhands.storage.conversation.file_conversation_store import FileConversationStore

from .llm import LLM
from .persistence import append_event_jsonl
from .tool import (
    Tool,
    runtime_execute_bash_tool,
    runtime_file_read_tool,
    runtime_file_write_tool,
)
from .types import ConversationStatus, SDKEvent, ToolResult


class _NoOpEventStream(EventStream):
    def __init__(self, sid: str, file_store: Any, user_id: str | None = None):
        # Initialize base EventStore layer without starting queue threads for no-op usage
        super().__init__(sid=sid, file_store=file_store, user_id=user_id)

    def subscribe(
        self, subscriber_id: EventStreamSubscriber, callback, callback_id: str
    ) -> None:  # type: ignore[override]
        # Do not start subscriber threads in SDK mode
        return

    def add_event(self, event, source) -> None:  # type: ignore[override]
        # Suppress legacy event writes
        return


def _default_runtime(noop_stream: EventStream) -> Runtime:
    config = OpenHandsConfig()
    llm_registry = LLMRegistry(config)
    runtime = CLIRuntime(
        config=config, event_stream=noop_stream, llm_registry=llm_registry
    )
    return runtime


@dataclass
class Agent:
    llm: LLM
    tools: list[Tool]
    microagents: list[str] = field(default_factory=list)
    system_prompt: str | None = None
    system_prompt_extensions: list[str] = field(default_factory=list)


class Conversation:
    def __init__(
        self,
        agent: Agent,
        runtime: Runtime | None = None,
        metadata_store: FileConversationStore | None = None,
        conversation_id: str | None = None,
        user_id: str | None = None,
    ) -> None:
        self.agent = agent
        self.conversation_id = conversation_id or str(uuid.uuid4())
        self.status_value = ConversationStatus.IDLE
        self.callbacks: list[Callable[[SDKEvent], None]] = []
        self.messages: list[dict[str, Any]] = []
        # Event persistence (always on, fixed location under ~/.openhands/conversations)
        import os

        home = os.path.expanduser('~')
        base = os.path.join(home, '.openhands', 'conversations')
        os.makedirs(os.path.join(base, self.conversation_id), exist_ok=True)
        self.jsonl_path = os.path.join(base, self.conversation_id, 'sdk_events.jsonl')
        # No-op event stream + runtime
        from openhands.storage.local import LocalFileStore

        self._event_stream = _NoOpEventStream(
            sid=self.conversation_id, file_store=LocalFileStore('.'), user_id=user_id
        )
        self.runtime = runtime or _default_runtime(self._event_stream)
        self._thread: threading.Thread | None = None
        # Attach handlers to runtime-backed tools
        self._attach_runtime_handlers()
        # Load and persist system_message at loop start for reproducibility
        from .system_prompt_loader import load_codeact_system_prompt

        sys_prompt = self.agent.system_prompt or load_codeact_system_prompt(render=True)
        if self.agent.system_prompt_extensions:
            sys_prompt = (
                sys_prompt.rstrip()
                + '\n\n'
                + '\n\n'.join(self.agent.system_prompt_extensions)
            )
        self.messages.append({'role': 'system', 'content': sys_prompt})
        self._emit(
            SDKEvent(
                type='system_message',
                ts=datetime.utcnow(),
                conversation_id=self.conversation_id,
                data={'text': sys_prompt},
            )
        )

    def _emit(self, evt: SDKEvent) -> None:
        if self.jsonl_path:
            append_event_jsonl(self.jsonl_path, evt)
        for cb in list(self.callbacks):
            try:
                cb(evt)
            except Exception:
                pass

    def register_callback(self, fn: Callable[[SDKEvent], None]) -> None:
        self.callbacks.append(fn)

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self.status_value = ConversationStatus.RUNNING
        # Ensure runtime is connected before tools are used
        try:
            import asyncio

            loop = None
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None
            if loop and loop.is_running():
                loop.create_task(self.runtime.connect())  # type: ignore[attr-defined]
            else:
                asyncio.run(self.runtime.connect())  # type: ignore[attr-defined]
        except Exception:
            pass
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self.status_value = ConversationStatus.CANCELED

    def _reconstruct_messages_from_events(
        self, events: list[SDKEvent]
    ) -> list[dict[str, Any]]:
        msgs: list[dict[str, Any]] = []
        pending_tool_calls: list[dict[str, Any]] = []
        pending_ids: set[str] = set()
        assistant_flushed: bool = False
        for evt in events:
            if evt.type == 'system_message':
                text = evt.data.get('text', '')
                if text:
                    msgs.append({'role': 'system', 'content': text})
                    # System message should be at the beginning; if not first, we'll keep order as-is
            elif evt.type == 'user_message':
                # New user input starts a new exchange; clear pending tool call batch
                pending_tool_calls.clear()
                pending_ids.clear()
                assistant_flushed = False
                msgs.append({'role': 'user', 'content': evt.data.get('text', '')})
            elif evt.type == 'assistant_message':
                # A text assistant message typically ends a tool-call batch; reset pending state
                text = evt.data.get('text', '')
                if text:
                    msgs.append({'role': 'assistant', 'content': text})
                pending_tool_calls.clear()
                pending_ids.clear()
                assistant_flushed = False
            elif evt.type == 'tool_call':
                tool_call_id = evt.data.get('tool_call_id') or str(uuid.uuid4())
                name = evt.data.get('name')
                args = evt.data.get('arguments') or {}
                # If a new batch starts after flush, reset
                if assistant_flushed and tool_call_id not in pending_ids:
                    pending_tool_calls.clear()
                    pending_ids.clear()
                    assistant_flushed = False
                pending_ids.add(tool_call_id)
                pending_tool_calls.append(
                    {
                        'id': tool_call_id,
                        'type': 'function',
                        'function': {
                            'name': name,
                            'arguments': json.dumps(args),
                        },
                    }
                )
            elif evt.type == 'tool_result':
                tool_call_id = evt.data.get('tool_call_id')
                # Before first tool_result in a batch, inject the synthesized assistant tool_calls message
                if pending_tool_calls and not assistant_flushed:
                    msgs.append(
                        {
                            'role': 'assistant',
                            'content': '',
                            'tool_calls': pending_tool_calls.copy(),
                        }
                    )
                    assistant_flushed = True
                tr = ToolResult(
                    status=evt.data.get('status', 'ok'),
                    output=evt.data.get('output'),
                    error=evt.data.get('error'),
                )
                if tool_call_id:
                    msgs.append(
                        {
                            'role': 'tool',
                            'content': json.dumps(tr.model_dump()),
                            'tool_call_id': tool_call_id,
                        }
                    )
        return msgs

    def autoresume_from_path(self, jsonl_path: str) -> None:
        from .persistence import read_events_jsonl

        events = read_events_jsonl(jsonl_path)
        self.messages = self._reconstruct_messages_from_events(events)

    def autoresume_latest(self) -> bool:
        # Locate ~/.openhands/conversations/<id>/sdk_events.jsonl with newest last ts
        import glob
        import os

        from .persistence import read_events_jsonl

        home = os.path.expanduser('~')
        base = os.path.join(home, '.openhands', 'conversations')
        if not os.path.isdir(base):
            return False
        candidates = []
        for conv_dir in glob.glob(os.path.join(base, '*')):
            jl = os.path.join(conv_dir, 'sdk_events.jsonl')
            if not os.path.exists(jl):
                continue
            try:
                evs = read_events_jsonl(jl)
                if not evs:
                    continue
                last_ts = evs[-1].ts
                candidates.append((last_ts, jl))
            except Exception:
                continue
        if not candidates:
            return False
        candidates.sort(key=lambda x: x[0], reverse=True)
        newest = candidates[0][1]
        self.autoresume_from_path(newest)
        return True

    def status(self) -> ConversationStatus:
        return self.status_value

    def send_message(self, text: str) -> None:
        evt = SDKEvent(
            type='user_message',
            ts=datetime.utcnow(),
            conversation_id=self.conversation_id,
            data={'text': text},
        )
        self._emit(evt)
        self.messages.append({'role': 'user', 'content': text})
        # Wake loop by setting status to RUNNING
        self.status_value = ConversationStatus.RUNNING

    def _attach_runtime_handlers(self) -> None:
        def run_bash(payload: dict) -> ToolResult:
            cmd = payload['command']
            timeout = payload.get('timeout')
            action = CmdRunAction(command=cmd)
            if timeout:
                action.set_hard_timeout(float(timeout))
            obs = self.runtime.run(action)  # type: ignore[arg-type]
            if isinstance(obs, CmdOutputObservation):
                return ToolResult(
                    status='ok',
                    output={'stdout': obs.content, 'exit_code': obs.exit_code},
                )
            if isinstance(obs, ErrorObservation):
                return ToolResult(status='error', error=obs.content)
            return ToolResult(status='ok', output=None)

        def file_read(payload: dict) -> ToolResult:
            path = payload['path']
            view_range = payload.get('view_range')
            action = FileReadAction(path=path, view_range=view_range)
            obs = self.runtime.read(action)  # type: ignore[arg-type]
            if isinstance(obs, FileReadObservation):
                return ToolResult(
                    status='ok', output={'path': path, 'content': obs.content}
                )
            if isinstance(obs, ErrorObservation):
                return ToolResult(status='error', error=obs.content)
            return ToolResult(status='ok', output=None)

        def file_write(payload: dict) -> ToolResult:
            path = payload['path']
            content = payload['content']
            action = FileWriteAction(path=path, content=content)
            obs = self.runtime.write(action)  # type: ignore[arg-type]
            if isinstance(obs, FileWriteObservation):
                return ToolResult(status='ok', output={'path': path})
            if isinstance(obs, ErrorObservation):
                return ToolResult(status='error', error=obs.content)
            return ToolResult(status='ok', output=None)

        # Create working copies with handlers bound
        self.tools: list[Tool] = []
        for base in [
            runtime_execute_bash_tool,
            runtime_file_read_tool,
            runtime_file_write_tool,
        ]:
            tool = Tool(**base.model_dump())
            if tool.name == 'execute_bash':
                tool.handler = run_bash
            elif tool.name == 'file_read':
                tool.handler = file_read
            elif tool.name == 'file_write':
                tool.handler = file_write
            self.tools.append(tool)
        # Include user-provided tools afterwards
        self.tools.extend(self.agent.tools)

    def _run_loop(self) -> None:
        # Build initial system prompt
        system_parts: list[str] = []
        if self.agent.system_prompt:
            system_parts.append(self.agent.system_prompt)
        system_parts.extend(self.agent.system_prompt_extensions)
        if self.agent.microagents:
            system_parts.append('\n'.join(self.agent.microagents))
        if system_parts:
            sys_text = '\n\n'.join(system_parts)
            # Persist the system message for autoresume fidelity
            self._emit(
                SDKEvent(
                    type='system_message',
                    ts=datetime.utcnow(),
                    conversation_id=self.conversation_id,
                    data={'text': sys_text},
                )
            )
            self.messages.insert(0, {'role': 'system', 'content': sys_text})

        while True:
            if self.status_value in {
                ConversationStatus.CANCELED,
                ConversationStatus.FINISHED,
                ConversationStatus.ERROR,
            }:
                break
            if not self.messages or self.messages[-1]['role'] == 'assistant':
                # Wait for user input
                time.sleep(0.1)
                continue

            # Prepare tools for LLM
            tool_params = [t.to_param() for t in self.tools]
            try:
                resp = self.agent.llm.send(messages=self.messages, tools=tool_params)
            except Exception as e:
                self.status_value = ConversationStatus.ERROR
                self._emit(
                    SDKEvent(
                        type='error',
                        ts=datetime.utcnow(),
                        conversation_id=self.conversation_id,
                        data={'error': str(e)},
                    )
                )
                break

            choice = resp.get('choices', [{}])[0]
            msg = choice.get('message', {})
            tool_calls = msg.get('tool_calls') or []
            content = msg.get('content')

            if tool_calls:
                # Execute each tool synchronously
                for tc in tool_calls:
                    name = tc['function']['name']
                    args_str = tc['function'].get('arguments') or '{}'
                    try:
                        args = json.loads(args_str)
                    except Exception:
                        args = {}
                    tool_call_id = tc.get('id') or str(uuid.uuid4())
                    self._emit(
                        SDKEvent(
                            type='tool_call',
                            ts=datetime.utcnow(),
                            conversation_id=self.conversation_id,
                            data={
                                'name': name,
                                'arguments': args,
                                'tool_call_id': tool_call_id,
                            },
                        )
                    )

                    handler = next(
                        (t.handler for t in self.tools if t.name == name and t.handler),
                        None,
                    )
                    if handler is None:
                        result = ToolResult(
                            status='error', error=f'Unknown tool: {name}'
                        )
                    else:
                        result = handler(args)

                    self._emit(
                        SDKEvent(
                            type='tool_result',
                            ts=datetime.utcnow(),
                            conversation_id=self.conversation_id,
                            data={
                                'name': name,
                                'tool_call_id': tool_call_id,
                                'status': result.status,
                                'output': result.output,
                                'error': result.error,
                            },
                        )
                    )

                    # Append tool result for next LLM turn
                    self.messages.append(
                        {
                            'role': 'tool',
                            'content': json.dumps(result.model_dump()),
                            'tool_call_id': tool_call_id,
                        }
                    )
                # After executing tool(s), continue the loop to get next assistant turn
                continue

            # No tool calls: assistant message
            if isinstance(content, str) and content.strip():
                self.messages.append({'role': 'assistant', 'content': content})
                self._emit(
                    SDKEvent(
                        type='assistant_message',
                        ts=datetime.utcnow(),
                        conversation_id=self.conversation_id,
                        data={'text': content},
                    )
                )
                # Idle until next user message
                self.status_value = ConversationStatus.IDLE
                time.sleep(0.1)
            else:
                # Nothing meaningful returned; idle
                self.status_value = ConversationStatus.IDLE
                time.sleep(0.2)
