import asyncio
from pathlib import Path

from prompt_toolkit import print_formatted_text
from prompt_toolkit.shortcuts import clear, print_container
from prompt_toolkit.widgets import Frame, TextArea

from openhands.cli.settings import (
    display_settings,
    modify_llm_settings_advanced,
    modify_llm_settings_basic,
)
from openhands.cli.tui import (
    COLOR_GREY,
    UsageMetrics,
    cli_confirm,
    display_help,
    display_shutdown_message,
    display_status,
)
from openhands.cli.utils import (
    add_local_config_trusted_dir,
    get_local_config_trusted_dirs,
    read_file,
    write_to_file,
)
from openhands.core.config import (
    AppConfig,
)
from openhands.core.schema import AgentState
from openhands.events import EventSource
from openhands.events.action import (
    ChangeAgentStateAction,
    MessageAction,
)
from openhands.events.stream import EventStream
from openhands.storage.settings.file_settings_store import FileSettingsStore


async def handle_commands(
    command: str,
    event_stream: EventStream,
    usage_metrics: UsageMetrics,
    sid: str,
    config: AppConfig,
    current_dir: str,
    settings_store: FileSettingsStore,
) -> tuple[bool, bool, bool]:
    close_repl = False
    reload_microagents = False
    new_session_requested = False

    if command == '/exit':
        close_repl = handle_exit_command(
            event_stream,
            usage_metrics,
            sid,
        )
    elif command == '/help':
        handle_help_command()
    elif command == '/init':
        close_repl, reload_microagents = await handle_init_command(
            config, event_stream, current_dir
        )
    elif command == '/status':
        handle_status_command(usage_metrics, sid)
    elif command == '/new':
        close_repl, new_session_requested = handle_new_command(
            event_stream, usage_metrics, sid
        )
    elif command == '/settings':
        await handle_settings_command(config, settings_store)
    elif command == '/resume':
        close_repl, new_session_requested = await handle_resume_command(event_stream)
    else:
        close_repl = True
        action = MessageAction(content=command)
        event_stream.add_event(action, EventSource.USER)

    return close_repl, reload_microagents, new_session_requested


def handle_exit_command(
    event_stream: EventStream, usage_metrics: UsageMetrics, sid: str
) -> bool:
    close_repl = False

    confirm_exit = (
        cli_confirm('\nTerminate session?', ['Yes, proceed', 'No, dismiss']) == 0
    )

    if confirm_exit:
        event_stream.add_event(
            ChangeAgentStateAction(AgentState.STOPPED),
            EventSource.ENVIRONMENT,
        )
        display_shutdown_message(usage_metrics, sid)
        close_repl = True

    return close_repl


def handle_help_command():
    display_help()


async def handle_init_command(
    config: AppConfig, event_stream: EventStream, current_dir: str
) -> tuple[bool, bool]:
    REPO_MD_CREATE_PROMPT = """
        Please explore this repository. Create the file .openhands/microagents/repo.md with:
            - A description of the project
            - An overview of the file structure
            - Any information on how to run tests or other relevant commands
            - Any other information that would be helpful to a brand new developer
        Keep it short--just a few paragraphs will do.
    """
    close_repl = False
    reload_microagents = False

    if config.runtime == 'local':
        init_repo = await init_repository(current_dir)
        if init_repo:
            event_stream.add_event(
                MessageAction(content=REPO_MD_CREATE_PROMPT),
                EventSource.USER,
            )
            reload_microagents = True
            close_repl = True
    else:
        print_formatted_text(
            '\nRepository initialization through the CLI is only supported for local runtime.\n'
        )

    return close_repl, reload_microagents


def handle_status_command(usage_metrics: UsageMetrics, sid: str):
    display_status(usage_metrics, sid)


def handle_new_command(
    event_stream: EventStream, usage_metrics: UsageMetrics, sid: str
) -> tuple[bool, bool]:
    close_repl = False
    new_session_requested = False

    new_session_requested = (
        cli_confirm(
            '\nCurrent session will be terminated and you will lose the conversation history.\n\nContinue?',
            ['Yes, proceed', 'No, dismiss'],
        )
        == 0
    )

    if new_session_requested:
        close_repl = True
        new_session_requested = True
        event_stream.add_event(
            ChangeAgentStateAction(AgentState.STOPPED),
            EventSource.ENVIRONMENT,
        )
        display_shutdown_message(usage_metrics, sid)

    return close_repl, new_session_requested


async def handle_settings_command(
    config: AppConfig,
    settings_store: FileSettingsStore,
):
    display_settings(config)
    modify_settings = cli_confirm(
        '\nWhich settings would you like to modify?',
        [
            'Basic',
            'Advanced',
            'Go back',
        ],
    )

    if modify_settings == 0:
        await modify_llm_settings_basic(config, settings_store)
    elif modify_settings == 1:
        await modify_llm_settings_advanced(config, settings_store)


# FIXME: Currently there's an issue with the actual 'resume' behavior.
# Setting the agent state to RUNNING will currently freeze the agent without continuing with the rest of the task.
# This is a workaround to handle the resume command for the time being. Replace user message with the state change event once the issue is fixed.
async def handle_resume_command(
    event_stream: EventStream,
) -> tuple[bool, bool]:
    close_repl = True
    new_session_requested = False

    event_stream.add_event(
        MessageAction(content='continue'),
        EventSource.USER,
    )

    # event_stream.add_event(
    #     ChangeAgentStateAction(AgentState.RUNNING),
    #     EventSource.ENVIRONMENT,
    # )

    return close_repl, new_session_requested


async def init_repository(current_dir: str) -> bool:
    repo_file_path = Path(current_dir) / '.openhands' / 'microagents' / 'repo.md'
    init_repo = False

    if repo_file_path.exists():
        try:
            content = await asyncio.get_event_loop().run_in_executor(
                None, read_file, repo_file_path
            )

            print_formatted_text(
                'Repository instructions file (repo.md) already exists.\n'
            )

            container = Frame(
                TextArea(
                    text=content,
                    read_only=True,
                    style=COLOR_GREY,
                    wrap_lines=True,
                ),
                title='Repository Instructions (repo.md)',
                style=f'fg:{COLOR_GREY}',
            )
            print_container(container)
            print_formatted_text('')  # Add a newline after the frame

            init_repo = (
                cli_confirm(
                    'Do you want to re-initialize?',
                    ['Yes, re-initialize', 'No, dismiss'],
                )
                == 0
            )

            if init_repo:
                write_to_file(repo_file_path, '')
        except Exception:
            print_formatted_text('Error reading repository instructions file (repo.md)')
            init_repo = False
    else:
        print_formatted_text(
            '\nRepository instructions file will be created by exploring the repository.\n'
        )

        init_repo = (
            cli_confirm(
                'Do you want to proceed?',
                ['Yes, create', 'No, dismiss'],
            )
            == 0
        )

    return init_repo


def check_folder_security_agreement(config: AppConfig, current_dir):
    # Directories trusted by user for the CLI to use as workspace
    # Config from ~/.openhands/config.toml overrides the app config

    app_config_trusted_dirs = config.sandbox.trusted_dirs
    local_config_trusted_dirs = get_local_config_trusted_dirs()

    trusted_dirs = local_config_trusted_dirs
    if not local_config_trusted_dirs:
        trusted_dirs = app_config_trusted_dirs

    is_trusted = current_dir in trusted_dirs

    if not is_trusted:
        security_frame = Frame(
            TextArea(
                text=(
                    f' Do you trust the files in this folder?\n\n'
                    f'   {current_dir}\n\n'
                    ' OpenHands may read and execute files in this folder with your permission.'
                ),
                style=COLOR_GREY,
                read_only=True,
                wrap_lines=True,
            ),
            style=f'fg:{COLOR_GREY}',
        )

        clear()
        print_container(security_frame)
        print_formatted_text('')

        confirm = (
            cli_confirm('Do you wish to continue?', ['Yes, proceed', 'No, exit']) == 0
        )

        if confirm:
            add_local_config_trusted_dir(current_dir)

        return confirm

    return True
