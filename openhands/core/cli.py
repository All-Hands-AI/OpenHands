import asyncio
import logging
import sys
from uuid import uuid4

from prompt_toolkit import PromptSession, print_formatted_text
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.formatted_text import HTML, FormattedText
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.shortcuts import print_container
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import Frame, TextArea

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
from openhands.llm.metrics import Metrics

# Color and styling constants
COLOR_GOLD = '#FFD700'
COLOR_GREY = '#808080'
DEFAULT_STYLE = Style.from_dict(
    {
        'gold': COLOR_GOLD,
        'grey': COLOR_GREY,
        'prompt': f'{COLOR_GOLD} bold',
    }
)

COMMANDS = {
    '/exit': 'Exit the application',
    '/help': 'Display available commands',
    '/init': 'Initialize a new repository',
}


class CommandCompleter(Completer):
    """Custom completer for commands."""

    def get_completions(self, document, complete_event):
        text = document.text

        # Only show completions if the user has typed '/'
        if text.startswith('/'):
            # If just '/' is typed, show all commands
            if text == '/':
                for command, description in COMMANDS.items():
                    yield Completion(
                        command[1:],  # Remove the leading '/' as it's already typed
                        start_position=0,
                        display=f'{command} - {description}',
                    )
            # Otherwise show matching commands
            else:
                for command, description in COMMANDS.items():
                    if command.startswith(text):
                        yield Completion(
                            command[len(text) :],  # Complete the remaining part
                            start_position=0,
                            display=f'{command} - {description}',
                        )


class UsageMetrics:
    def __init__(self):
        self.total_cost: float = 0.00
        self.total_input_tokens: int = 0
        self.total_output_tokens: int = 0
        self.total_cache_read: int = 0
        self.total_cache_write: int = 0


prompt_session = PromptSession(style=DEFAULT_STYLE, completer=CommandCompleter())


def display_message(message: str):
    message = message.strip()

    if message:
        print_formatted_text(
            FormattedText(
                [
                    ('', '\n'),
                    (COLOR_GOLD, message),
                    ('', '\n'),
                ]
            )
        )


def display_command(command: str):
    container = Frame(
        TextArea(
            text=command,
            read_only=True,
            style=COLOR_GREY,
            wrap_lines=True,
        ),
        title='Command Run',
        style=f'fg:{COLOR_GREY}',
    )
    print_container(container)
    print_formatted_text('')


def display_confirmation(confirmation_state: ActionConfirmationStatus):
    status_map = {
        ActionConfirmationStatus.CONFIRMED: ('ansigreen', '✅'),
        ActionConfirmationStatus.REJECTED: ('ansired', '❌'),
        ActionConfirmationStatus.AWAITING_CONFIRMATION: ('ansiyellow', '⏳'),
    }
    color, icon = status_map.get(confirmation_state, ('ansiyellow', ''))

    print_formatted_text(
        FormattedText(
            [
                (color, f'{icon} '),
                (color, str(confirmation_state)),
                ('', '\n'),
            ]
        )
    )


def display_command_output(output: str):
    lines = output.split('\n')
    formatted_lines = []
    for line in lines:
        if line.startswith('[Python Interpreter') or line.startswith('openhands@'):
            # TODO: clean this up once we clean up terminal output
            continue
        formatted_lines.append(line)
        formatted_lines.append('\n')

    # Remove the last newline if it exists
    if formatted_lines:
        formatted_lines.pop()

    container = Frame(
        TextArea(
            text=''.join(formatted_lines),
            read_only=True,
            style=COLOR_GREY,
            wrap_lines=True,
        ),
        title='Command Output',
        style=f'fg:{COLOR_GREY}',
    )
    print_container(container)
    print_formatted_text('')


def display_file_edit(event: FileEditAction | FileEditObservation):
    container = Frame(
        TextArea(
            text=f'{event}',
            read_only=True,
            style=COLOR_GREY,
            wrap_lines=True,
        ),
        title='File Edit',
        style=f'fg:{COLOR_GREY}',
    )
    print_container(container)
    print_formatted_text('')


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


def display_help(style=DEFAULT_STYLE):
    version = '0.1.0'  # TODO: link the actual version
    print_formatted_text(HTML(f'\n<grey>OpenHands CLI v{version}</grey>'), style=style)

    print('\nSample tasks:')
    print('- Create a simple todo list application')
    print('- Create a simple web server')
    print('- Create a REST API')
    print('- Create a chat application')

    print_formatted_text(HTML('\nInteractive commands:'), style=style)
    for command, description in COMMANDS.items():
        print_formatted_text(
            HTML(f'<gold><b>{command}</b></gold> - <grey>{description}</grey>'),
            style=style,
        )
    print('')


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
                '> ',
            )
        return message
    except KeyboardInterrupt:
        return '/exit'
    except EOFError:
        return '/exit'


async def read_confirmation_input():
    try:
        confirmation = await prompt_session.prompt_async(
            'Confirm action (possible security risk)? (y/n) > ',
        )
        return confirmation.lower() == 'y'
    except (KeyboardInterrupt, EOFError):
        return False


def update_usage_metrics(event: Event, usage_metrics: UsageMetrics):
    """Updates the UsageMetrics object with data from an event's llm_metrics."""
    if hasattr(event, 'llm_metrics'):
        llm_metrics: Metrics | None = getattr(event, 'llm_metrics', None)
        if llm_metrics:
            # Safely get accumulated_cost
            cost = getattr(llm_metrics, 'accumulated_cost', 0)
            # Ensure cost is a number before adding
            usage_metrics.total_cost += cost if isinstance(cost, float) else 0

            # Safely get token usage details object/dict
            token_usage = getattr(llm_metrics, 'accumulated_token_usage', None)
            if token_usage:
                # Assume object access using getattr, providing defaults
                prompt_tokens = getattr(token_usage, 'prompt_tokens', 0)
                completion_tokens = getattr(token_usage, 'completion_tokens', 0)
                cache_read = getattr(token_usage, 'cache_read_tokens', 0)
                cache_write = getattr(token_usage, 'cache_write_tokens', 0)

                # Ensure tokens are numbers before adding
                usage_metrics.total_input_tokens += (
                    prompt_tokens if isinstance(prompt_tokens, int) else 0
                )
                usage_metrics.total_output_tokens += (
                    completion_tokens if isinstance(completion_tokens, int) else 0
                )
                usage_metrics.total_cache_read += (
                    cache_read if isinstance(cache_read, int) else 0
                )
                usage_metrics.total_cache_write += (
                    cache_write if isinstance(cache_write, int) else 0
                )


def shutdown(usage_metrics: UsageMetrics, session_id: str):
    cost_str = f'${usage_metrics.total_cost:.6f}'
    input_tokens_str = f'{usage_metrics.total_input_tokens:,}'
    cache_read_str = f'{usage_metrics.total_cache_read:,}'
    cache_write_str = f'{usage_metrics.total_cache_write:,}'
    output_tokens_str = f'{usage_metrics.total_output_tokens:,}'
    total_tokens_str = (
        f'{usage_metrics.total_input_tokens + usage_metrics.total_output_tokens:,}'
    )

    labels_and_values = [
        ('   Total Cost (USD):', cost_str),
        ('   Total Input Tokens:', input_tokens_str),
        ('      Cache Hits:', cache_read_str),
        ('      Cache Writes:', cache_write_str),
        ('   Total Output Tokens:', output_tokens_str),
        ('   Total Tokens:', total_tokens_str),
    ]

    # Calculate max widths for alignment
    max_label_width = max(len(label) for label, _ in labels_and_values)
    max_value_width = max(len(value) for _, value in labels_and_values)

    # Construct the summary text with aligned columns
    summary_lines = [
        f'{label:<{max_label_width}} {value:>{max_value_width}}'
        for label, value in labels_and_values
    ]
    summary_text = '\n'.join(summary_lines)

    container = Frame(
        TextArea(
            text=summary_text,
            read_only=True,
            style=COLOR_GREY,
            wrap_lines=True,
        ),
        title='Session Summary',
        style=f'fg:{COLOR_GREY}',
    )
    print_container(container)
    print_formatted_text(HTML(f'\n<grey>Closed session {session_id}</grey>\n'))


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

    usage_metrics = UsageMetrics()

    async def prompt_for_next_task():
        next_message = await read_prompt_input(config.cli_multiline_input)
        if not next_message.strip():
            await prompt_for_next_task()
        if next_message == '/exit':
            event_stream.add_event(
                ChangeAgentStateAction(AgentState.STOPPED), EventSource.ENVIRONMENT
            )
            shutdown(usage_metrics, sid)
            return
        if next_message == '/help':
            display_help()
            await prompt_for_next_task()
        if next_message == '/init':
            # TODO: Implement init command
            await prompt_for_next_task()
        action = MessageAction(content=next_message)
        event_stream.add_event(action, EventSource.USER)

    async def on_event_async(event: Event):
        display_event(event, config)
        update_usage_metrics(event, usage_metrics)
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
