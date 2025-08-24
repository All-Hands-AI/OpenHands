from __future__ import annotations

import argparse
import json
import os
import time
from typing import Any

from openhands.core.logger import openhands_logger as logger
from openhands.storage.conversation.file_conversation_store import (
    FileConversationStore,
)
from openhands.storage.local import LocalFileStore

from .conversation import Agent, Conversation
from .llm import LLM, LLMConfig
from .types import SDKEvent


def load_settings(default_path: str) -> dict[str, Any]:
    path = os.path.expanduser(default_path)
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f'Failed to load settings from {path}: {e}')
    return {}


def print_logo() -> None:
    logo = r"""
   ___              _   _                 _
  / _ \  ___  _ __ | |_(_)_ __   __ _  __| | ___ _ __
 | | | |/ _ \| '_ \| __| | '_ \ / _` |/ _` |/ _ \ '__|
 | |_| | (_) | | | | |_| | | | | (_| | (_| |  __/ |
  \___/ \___/|_| |_|\__|_|_| |_|\__,_|\__,_|\___|_|
    OpenHands Minimal SDK
    """
    print(logo)


def run_headless(conversation: Conversation, prompt: str | None) -> int:
    def _snippet(val: Any) -> str:
        try:
            s = val if isinstance(val, str) else json.dumps(val)
        except Exception:
            s = str(val)
        lines = s.splitlines()
        s = '\n'.join(lines[:10])
        if len(lines) > 10 or len(s) > 200:
            s = s[:200] + '...'
        return s

    last_error: list[str] = []

    def cb(evt: SDKEvent) -> None:
        ts = evt.ts.isoformat()
        if evt.type == 'assistant_message':
            print(f'[{ts}] assistant: {evt.data.get("text", "")}')
        elif evt.type == 'tool_call':
            name = evt.data.get('name')
            args = evt.data.get('arguments')
            print(f'[{ts}] tool_call {name} args={_snippet(args)}')
        elif evt.type == 'tool_result':
            status = evt.data.get('status')
            output = evt.data.get('output')
            print(f'[{ts}] tool_result {status} output={_snippet(output)}')
        elif evt.type == 'error':
            msg = evt.data.get('error') if isinstance(evt.data, dict) else str(evt.data)
            one = str(msg).splitlines()[0] if msg else 'unknown error'
            print(f'[error] {one}')
            last_error.clear()
            last_error.append(one)
        else:
            print(f'[{ts}] {evt.type}: {evt.data}')

    conversation.register_callback(cb)
    print(
        '\nWARNING: Using CLIRuntime. Commands will execute on your local machine. Use with caution.\n'
    )
    try:
        if not conversation.agent.llm.supports_function_calling():
            print(
                'Warning: The configured model may not support function-calling; proceeding anyway.'
            )
    except Exception:
        pass
    # If a prompt is provided, enqueue it before starting the loop
    if prompt:
        conversation.send_message(prompt)
    conversation.start()
    # Wait for completion or error
    while True:
        st = conversation.status().value
        if st == 'ERROR':
            return 1
        if st == 'IDLE':
            return 0
        time.sleep(0.2)


def run_tui(conversation: Conversation, autoresume: bool) -> int:
    print_logo()
    print('\nType /exit to quit.')
    if autoresume:
        print(
            '(Autoresume requested: latest conversation context will be loaded if available)'
        )

    def _snippet(val: Any) -> str:
        try:
            s = val if isinstance(val, str) else json.dumps(val)
        except Exception:
            s = str(val)
        lines = s.splitlines()
        s = '\n'.join(lines[:10])
        if len(lines) > 10 or len(s) > 200:
            s = s[:200] + '...'
        return s

    def cb(evt: SDKEvent) -> None:
        if evt.type == 'assistant_message':
            print(f'Assistant: {evt.data.get("text", "")}')
        elif evt.type == 'tool_call':
            name = evt.data.get('name')
            args = evt.data.get('arguments')
            print(f'[tool_call] {name} args={_snippet(args)}')
        elif evt.type == 'tool_result':
            status = evt.data.get('status')
            output = evt.data.get('output')
            print(f'[tool_result] {status} output={_snippet(output)}')
        elif evt.type == 'error':
            msg = evt.data.get('error') if isinstance(evt.data, dict) else str(evt.data)
            one = str(msg).splitlines()[0] if msg else 'unknown error'
            print(f'[error] {one}')

    conversation.register_callback(cb)
    print(
        '\nWARNING: Using CLIRuntime. Commands will execute on your local machine. Use with caution.\n'
    )
    try:
        if not conversation.agent.llm.supports_function_calling():
            print(
                'Warning: The configured model may not support function-calling; proceeding anyway.'
            )
    except Exception:
        pass
    conversation.start()

    while True:
        try:
            user_input = input('You: ').strip()
        except (EOFError, KeyboardInterrupt):
            user_input = '/exit'
        if user_input == '/exit':
            print('Exiting...')
            break
        if not user_input:
            continue
        conversation.send_message(user_input)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='OpenHands Minimal SDK TUI')
    parser.add_argument('--no-tui', action='store_true', help='Run headless mode')
    parser.add_argument('--model', type=str, default='gpt-4o-mini')
    parser.add_argument('--api-key', type=str, default=os.getenv('OPENAI_API_KEY'))
    parser.add_argument(
        '--settings', type=str, default='~/.openhands/settings_sdk.json'
    )

    parser.add_argument(
        '--autoresume', action='store_true', help='Resume most recent conversation'
    )
    parser.add_argument(
        '--prompt', type=str, default=None, help='Initial prompt (headless)'
    )

    args = parser.parse_args(argv)

    # Load settings file if present
    settings = load_settings(args.settings)
    model = args.model or settings.get('model')
    api_key = args.api_key or settings.get('api_key')

    if not model:
        print(
            'Model not configured. Please enter a model (e.g., openhands/o3 or gpt-4o-mini):'
        )
        model = input('model: ').strip()
    if not api_key:
        print('API key not configured. Please enter your API key:')
        api_key = input('api_key: ').strip()

    llm = LLM(LLMConfig(model=model, api_key=api_key))
    # Do not pass runtime tools here to avoid duplicates; Conversation will attach runtime-backed tools
    agent = Agent(
        llm=llm,
        tools=[],
    )

    # Prepare FileConversationStore for metadata if needed
    file_store = LocalFileStore(os.path.expanduser('~/.openhands'))
    metadata_store = FileConversationStore(file_store)

    conversation = Conversation(
        agent=agent,
        runtime=None,
        metadata_store=metadata_store,
        conversation_id=None,
    )

    # Autoresume if requested
    if args.autoresume:
        if conversation.autoresume_latest():
            print('Autoresume: loaded latest conversation context.')
        else:
            print('Autoresume requested, but no previous conversation found.')

    if args.no_tui:
        return run_headless(conversation, args.prompt)
    else:
        return run_tui(conversation, autoresume=args.autoresume)


if __name__ == '__main__':
    raise SystemExit(main())
