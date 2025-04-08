import asyncio
import logging
import sys
from uuid import uuid4

from prompt_toolkit import PromptSession, print_formatted_text
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.key_binding import KeyBindings

import openhands.agenthub  # noqa F401 (we import this to get the agents registered)
from openhands.core.config import (
    AppConfig,
    parse_arguments,
    setup_config_from_args,
)
from openhands.core.logger import openhands_logger as logger
from openhands.core.loop import run_agent_until_done
from openhands.core.schema import AgentState
from openhands.core.setup import (
    create_agent,
    create_controller,
    create_memory,
    create_runtime,
    initialize_repository_for_runtime,
)
from openhands.events import EventSource, EventStreamSubscriber
from openhands.events.action import (
    Action,
    ActionConfirmationStatus,
    ChangeAgentStateAction,
    CmdRunAction,
    FileEditAction,
    MessageAction,
)
from openhands.events.event import Event
from openhands.events.observation import (
    AgentStateChangedObservation,
    CmdOutputObservation,
    FileEditObservation,
)
from openhands.io import read_task

prompt_session = PromptSession()


def display_message(message: str):
    print_formatted_text(
        FormattedText(
            [
                ('ansiyellow', '🤖 '),
                ('ansiyellow', message),
                ('', '\n'),
            ]
        )
    )


def display_command(command: str):
    print_formatted_text(
        FormattedText(
            [
                ('', '❯ '),
                ('ansigreen', command),
                ('', '\n'),
            ]
        )
    )


def display_confirmation(confirmation_state: ActionConfirmationStatus):
    if confirmation_state == ActionConfirmationStatus.CONFIRMED:
        print_formatted_text(
            FormattedText(
                [
                    ('ansigreen', '✅ '),
                    ('ansigreen', str(confirmation_state)),
                    ('', '\n'),
                ]
            )
        )
    elif confirmation_state == ActionConfirmationStatus.REJECTED:
        print_formatted_text(
            FormattedText(
                [
                    ('ansired', '❌ '),
                    ('ansired', str(confirmation_state)),
                    ('', '\n'),
                ]
            )
        )
    else:
        print_formatted_text(
            FormattedText(
                [
                    ('ansiyellow', '⏳ '),
                    ('ansiyellow', str(confirmation_state)),
                    ('', '\n'),
                ]
            )
        )


def display_command_output(output: str):
    lines = output.split('\n')
    for line in lines:
        if line.startswith('[Python Interpreter') or line.startswith('openhands@'):
            # TODO: clean this up once we clean up terminal output
            continue
        print_formatted_text(FormattedText([('ansiblue', line)]))
    print_formatted_text('')


def display_file_edit(event: FileEditAction | FileEditObservation):
    print_formatted_text(
        FormattedText(
            [
                ('ansigreen', str(event)),
                ('', '\n'),
            ]
        )
    )


def display_event(event: Event, config: AppConfig):
    if isinstance(event, Action):
        if hasattr(event, 'thought'):
            display_message(event.thought)
    if isinstance(event, MessageAction):
        if event.source == EventSource.AGENT:
            display_message(event.content)
    if isinstance(event, CmdRunAction):
        display_command(event.command)
    if isinstance(event, CmdOutputObservation):
        display_command_output(event.content)
    if isinstance(event, FileEditAction):
        display_file_edit(event)
    if isinstance(event, FileEditObservation):
        display_file_edit(event)
    if hasattr(event, 'confirmation_state') and config.security.confirmation_mode:
        display_confirmation(event.confirmation_state)


async def read_prompt_input(multiline=False):
    try:
        if multiline:
            kb = KeyBindings()

            @kb.add('c-d')
            def _(event):
                event.current_buffer.validate_and_handle()

            message = await prompt_session.prompt_async(
                'Enter your message and press Ctrl+D to finish:\n',
                multiline=True,
                key_bindings=kb,
            )
        else:
            message = await prompt_session.prompt_async(
                '>> ',
            )
        return message
    except KeyboardInterrupt:
        return 'exit'
    except EOFError:
        return 'exit'


async def read_confirmation_input():
    try:
        confirmation = await prompt_session.prompt_async(
            'Confirm action (possible security risk)? (y/n) >> ',
        )
        return confirmation.lower() == 'y'
    except (KeyboardInterrupt, EOFError):
        return False


async def main(loop: asyncio.AbstractEventLoop):
    """Runs the agent in CLI mode."""

    args = parse_arguments()

    logger.setLevel(logging.WARNING)

    # Load config from toml and override with command line arguments
    config: AppConfig = setup_config_from_args(args)

    # Read task from file, CLI args, or stdin
    task_str = read_task(args, config.cli_multiline_input)

    # If we have a task, create initial user action
    initial_user_action = MessageAction(content=task_str) if task_str else None

    sid = str(uuid4())
    display_message(f'Session ID: {sid}')

    agent = create_agent(config)

    runtime = create_runtime(
        config,
        sid=sid,
        headless_mode=True,
        agent=agent,
    )

    controller, _ = create_controller(agent, runtime, config)

    event_stream = runtime.event_stream

    async def prompt_for_next_task():
        next_message = await read_prompt_input(config.cli_multiline_input)
        if not next_message.strip():
            await prompt_for_next_task()
        if next_message == 'exit':
            event_stream.add_event(
                ChangeAgentStateAction(AgentState.STOPPED), EventSource.ENVIRONMENT
            )
            return
        action = MessageAction(content=next_message)
        event_stream.add_event(action, EventSource.USER)

    async def on_event_async(event: Event):
        display_event(event, config)
        if isinstance(event, AgentStateChangedObservation):
            if event.agent_state in [
                AgentState.AWAITING_USER_INPUT,
                AgentState.FINISHED,
            ]:
                await prompt_for_next_task()
            if event.agent_state == AgentState.AWAITING_USER_CONFIRMATION:
                user_confirmed = await read_confirmation_input()
                if user_confirmed:
                    event_stream.add_event(
                        ChangeAgentStateAction(AgentState.USER_CONFIRMED),
                        EventSource.USER,
                    )
                else:
                    event_stream.add_event(
                        ChangeAgentStateAction(AgentState.USER_REJECTED),
                        EventSource.USER,
                    )

    def on_event(event: Event) -> None:
        loop.create_task(on_event_async(event))

    event_stream.subscribe(EventStreamSubscriber.MAIN, on_event, str(uuid4()))

    await runtime.connect()

    # Initialize repository if needed
    repo_directory = None
    if config.sandbox.selected_repo:
        repo_directory = initialize_repository_for_runtime(
            runtime,
            selected_repository=config.sandbox.selected_repo,
        )

    # when memory is created, it will load the microagents from the selected repository
    memory = create_memory(
        runtime=runtime,
        event_stream=event_stream,
        sid=sid,
        selected_repository=config.sandbox.selected_repo,
        repo_directory=repo_directory,
    )

    if initial_user_action:
        # If there's an initial user action, enqueue it and do not prompt again
        event_stream.add_event(initial_user_action, EventSource.USER)
    else:
        # Otherwise prompt for the user's first message right away
        asyncio.create_task(prompt_for_next_task())

    await run_agent_until_done(
        controller, runtime, memory, [AgentState.STOPPED, AgentState.ERROR]
    )


if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main(loop))
    except KeyboardInterrupt:
        print('Received keyboard interrupt, shutting down...')
    except ConnectionRefusedError as e:
        print(f'Connection refused: {e}')
        sys.exit(1)
    except Exception as e:
        print(f'An error occurred: {e}')
        sys.exit(1)
    finally:
        try:
            # Cancel all running tasks
            pending = asyncio.all_tasks(loop)
            for task in pending:
                task.cancel()
            # Wait for all tasks to complete with a timeout
            loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            loop.close()
        except Exception as e:
            print(f'Error during cleanup: {e}')
            sys.exit(1)
