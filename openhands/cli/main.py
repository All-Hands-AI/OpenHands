import asyncio
import logging
import os
import sys

from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.shortcuts import clear

import openhands.agenthub  # noqa F401 (we import this to get the agents registered)
import openhands.cli.suppress_warnings  # noqa: F401
from openhands.cli.commands import (
    check_folder_security_agreement,
    handle_commands,
)
from openhands.cli.settings import modify_llm_settings_basic
from openhands.cli.shell_config import (
    ShellConfigManager,
    add_aliases_to_shell_config,
    aliases_exist_in_shell_config,
)
from openhands.cli.tui import (
    UsageMetrics,
    cli_confirm,
    display_agent_running_message,
    display_banner,
    display_event,
    display_initial_user_prompt,
    display_initialization_animation,
    display_runtime_initialization_message,
    display_welcome_message,
    read_confirmation_input,
    read_prompt_input,
    start_pause_listener,
    stop_pause_listener,
    update_streaming_output,
)
from openhands.cli.utils import (
    update_usage_metrics,
)
from openhands.cli.vscode_extension import attempt_vscode_extension_install
from openhands.controller import AgentController
from openhands.controller.agent import Agent
from openhands.core.config import (
    OpenHandsConfig,
    parse_arguments,
    setup_config_from_args,
)
from openhands.core.config.condenser_config import NoOpCondenserConfig
from openhands.core.config.mcp_config import OpenHandsMCPConfigImpl
from openhands.core.config.utils import finalize_config
from openhands.core.logger import openhands_logger as logger
from openhands.core.loop import run_agent_until_done
from openhands.core.schema import AgentState
from openhands.core.schema.exit_reason import ExitReason
from openhands.core.setup import (
    create_agent,
    create_controller,
    create_memory,
    create_runtime,
    generate_sid,
    initialize_repository_for_runtime,
)
from openhands.events import EventSource, EventStreamSubscriber
from openhands.events.action import (
    ChangeAgentStateAction,
    MessageAction,
)
from openhands.events.event import Event
from openhands.events.observation import (
    AgentStateChangedObservation,
)
from openhands.io import read_task
from openhands.mcp import add_mcp_tools_to_agent
from openhands.memory.condenser.impl.llm_summarizing_condenser import (
    LLMSummarizingCondenserConfig,
)
from openhands.microagent.microagent import BaseMicroagent
from openhands.runtime import get_runtime_cls
from openhands.runtime.base import Runtime
from openhands.storage.settings.file_settings_store import FileSettingsStore


async def cleanup_session(
    loop: asyncio.AbstractEventLoop,
    agent: Agent,
    runtime: Runtime,
    controller: AgentController,
) -> None:
    """Clean up all resources from the current session."""
    event_stream = runtime.event_stream
    end_state = controller.get_state()
    end_state.save_to_session(
        event_stream.sid,
        event_stream.file_store,
        event_stream.user_id,
    )

    try:
        current_task = asyncio.current_task(loop)
        pending = [task for task in asyncio.all_tasks(loop) if task is not current_task]

        if pending:
            done, pending_set = await asyncio.wait(set(pending), timeout=2.0)
            pending = list(pending_set)

        for task in pending:
            task.cancel()

        agent.reset()
        runtime.close()
        await controller.close()

    except Exception as e:
        logger.error(f'Error during session cleanup: {e}')


async def run_session(
    loop: asyncio.AbstractEventLoop,
    config: OpenHandsConfig,
    settings_store: FileSettingsStore,
    current_dir: str,
    task_content: str | None = None,
    conversation_instructions: str | None = None,
    session_name: str | None = None,
    skip_banner: bool = False,
) -> bool:
    reload_microagents = False
    new_session_requested = False
    exit_reason = ExitReason.INTENTIONAL

    sid = generate_sid(config, session_name)
    is_loaded = asyncio.Event()
    is_paused = asyncio.Event()  # Event to track agent pause requests
    always_confirm_mode = False  # Flag to enable always confirm mode

    # Show runtime initialization message
    display_runtime_initialization_message(config.runtime)

    # Show Initialization loader
    loop.run_in_executor(
        None, display_initialization_animation, 'Initializing...', is_loaded
    )

    agent = create_agent(config)
    runtime = create_runtime(
        config,
        sid=sid,
        headless_mode=True,
        agent=agent,
    )

    def stream_to_console(output: str) -> None:
        # Instead of printing to stdout, pass the string to the TUI module
        update_streaming_output(output)

    runtime.subscribe_to_shell_stream(stream_to_console)

    controller, initial_state = create_controller(agent, runtime, config)

    event_stream = runtime.event_stream

    usage_metrics = UsageMetrics()

    async def prompt_for_next_task(agent_state: str) -> None:
        nonlocal reload_microagents, new_session_requested, exit_reason
        while True:
            next_message = await read_prompt_input(
                config, agent_state, multiline=config.cli_multiline_input
            )

            if not next_message.strip():
                continue

            (
                close_repl,
                reload_microagents,
                new_session_requested,
                exit_reason,
            ) = await handle_commands(
                next_message,
                event_stream,
                usage_metrics,
                sid,
                config,
                current_dir,
                settings_store,
            )

            if close_repl:
                return

    async def on_event_async(event: Event) -> None:
        nonlocal reload_microagents, is_paused, always_confirm_mode
        display_event(event, config)
        update_usage_metrics(event, usage_metrics)

        if isinstance(event, AgentStateChangedObservation):
            if event.agent_state not in [AgentState.RUNNING, AgentState.PAUSED]:
                await stop_pause_listener()

        if isinstance(event, AgentStateChangedObservation):
            if event.agent_state in [
                AgentState.AWAITING_USER_INPUT,
                AgentState.FINISHED,
            ]:
                # If the agent is paused, do not prompt for input as it's already handled by PAUSED state change
                if is_paused.is_set():
                    return

                # Reload microagents after initialization of repo.md
                if reload_microagents:
                    microagents: list[BaseMicroagent] = (
                        runtime.get_microagents_from_selected_repo(None)
                    )
                    memory.load_user_workspace_microagents(microagents)
                    reload_microagents = False
                await prompt_for_next_task(event.agent_state)

            if event.agent_state == AgentState.AWAITING_USER_CONFIRMATION:
                # If the agent is paused, do not prompt for confirmation
                # The confirmation step will re-run after the agent has been resumed
                if is_paused.is_set():
                    return

                if always_confirm_mode:
                    event_stream.add_event(
                        ChangeAgentStateAction(AgentState.USER_CONFIRMED),
                        EventSource.USER,
                    )
                    return

                confirmation_status = await read_confirmation_input(config)
                if confirmation_status == 'yes' or confirmation_status == 'always':
                    event_stream.add_event(
                        ChangeAgentStateAction(AgentState.USER_CONFIRMED),
                        EventSource.USER,
                    )
                else:
                    event_stream.add_event(
                        ChangeAgentStateAction(AgentState.USER_REJECTED),
                        EventSource.USER,
                    )

                # Set the always_confirm_mode flag if the user wants to always confirm
                if confirmation_status == 'always':
                    always_confirm_mode = True

            if event.agent_state == AgentState.PAUSED:
                is_paused.clear()  # Revert the event state before prompting for user input
                await prompt_for_next_task(event.agent_state)

            if event.agent_state == AgentState.RUNNING:
                display_agent_running_message()
                start_pause_listener(loop, is_paused, event_stream)

    def on_event(event: Event) -> None:
        loop.create_task(on_event_async(event))

    event_stream.subscribe(EventStreamSubscriber.MAIN, on_event, sid)

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
        conversation_instructions=conversation_instructions,
    )

    # Add MCP tools to the agent
    if agent.config.enable_mcp:
        # Add OpenHands' MCP server by default
        _, openhands_mcp_stdio_servers = (
            OpenHandsMCPConfigImpl.create_default_mcp_server_config(
                config.mcp_host, config, None
            )
        )

        runtime.config.mcp.stdio_servers.extend(openhands_mcp_stdio_servers)

        await add_mcp_tools_to_agent(agent, runtime, memory)

    # Clear loading animation
    is_loaded.set()

    # Clear the terminal
    clear()

    # Show OpenHands banner and session ID if not skipped
    if not skip_banner:
        display_banner(session_id=sid)

    welcome_message = 'What do you want to build?'  # from the application
    initial_message = ''  # from the user

    if task_content:
        initial_message = task_content

    # If we loaded a state, we are resuming a previous session
    if initial_state is not None:
        logger.info(f'Resuming session: {sid}')

        if initial_state.last_error:
            # If the last session ended in an error, provide a message.
            initial_message = (
                'NOTE: the last session ended with an error.'
                "Let's get back on track. Do NOT resume your task. Ask me about it."
            )
        else:
            # If we are resuming, we already have a task
            initial_message = ''
            welcome_message += '\nLoading previous conversation.'

    # Show OpenHands welcome
    display_welcome_message(welcome_message)

    # The prompt_for_next_task will be triggered if the agent enters AWAITING_USER_INPUT.
    # If the restored state is already AWAITING_USER_INPUT, on_event_async will handle it.

    if initial_message:
        display_initial_user_prompt(initial_message)
        event_stream.add_event(MessageAction(content=initial_message), EventSource.USER)
    else:
        # No session restored, no initial action: prompt for the user's first message
        asyncio.create_task(prompt_for_next_task(''))

    await run_agent_until_done(
        controller, runtime, memory, [AgentState.STOPPED, AgentState.ERROR]
    )

    await cleanup_session(loop, agent, runtime, controller)

    if exit_reason == ExitReason.INTENTIONAL:
        print_formatted_text('✅ Session terminated successfully.\n')
    else:
        print_formatted_text(f'⚠️ Session was interrupted: {exit_reason.value}\n')

    return new_session_requested


async def run_setup_flow(config: OpenHandsConfig, settings_store: FileSettingsStore):
    """Run the setup flow to configure initial settings.

    Returns:
        bool: True if settings were successfully configured, False otherwise.
    """
    # Display the banner with ASCII art first
    display_banner(session_id='setup')

    print_formatted_text(
        HTML('<grey>No settings found. Starting initial setup...</grey>\n')
    )

    # Use the existing settings modification function for basic setup
    await modify_llm_settings_basic(config, settings_store)


def run_alias_setup_flow(config: OpenHandsConfig) -> None:
    """Run the alias setup flow to configure shell aliases.

    Prompts the user to set up aliases for 'openhands' and 'oh' commands.
    Handles existing aliases by offering to keep or remove them.
    """
    print_formatted_text('')
    print_formatted_text(HTML('<gold>🚀 Welcome to OpenHands CLI!</gold>'))
    print_formatted_text('')

    # Check if aliases already exist
    if aliases_exist_in_shell_config():
        print_formatted_text(
            HTML(
                '<grey>We detected existing OpenHands aliases in your shell configuration.</grey>'
            )
        )
        print_formatted_text('')
        print_formatted_text(
            HTML(
                '<grey>  • <b>openhands</b> → uvx --python 3.12 --from openhands-ai openhands</grey>'
            )
        )
        print_formatted_text(
            HTML(
                '<grey>  • <b>oh</b> → uvx --python 3.12 --from openhands-ai openhands</grey>'
            )
        )
        print_formatted_text('')
        print_formatted_text(
            HTML('<ansigreen>✅ Aliases are already configured.</ansigreen>')
        )
        return  # Exit early since aliases already exist
    else:
        # No existing aliases, show the normal setup flow
        print_formatted_text(
            HTML('<grey>Would you like to set up convenient shell aliases?</grey>')
        )
        print_formatted_text('')
        print_formatted_text(
            HTML(
                '<grey>This will add the following aliases to your shell profile:</grey>'
            )
        )
        print_formatted_text(
            HTML(
                '<grey>  • <b>openhands</b> → uvx --python 3.12 --from openhands-ai openhands</grey>'
            )
        )
        print_formatted_text(
            HTML(
                '<grey>  • <b>oh</b> → uvx --python 3.12 --from openhands-ai openhands</grey>'
            )
        )
        print_formatted_text('')
        print_formatted_text(
            HTML(
                '<ansiyellow>⚠️  Note: This requires uv to be installed first.</ansiyellow>'
            )
        )
        print_formatted_text(
            HTML(
                '<ansiyellow>   Installation guide: https://docs.astral.sh/uv/getting-started/installation</ansiyellow>'
            )
        )
        print_formatted_text('')

        # Use cli_confirm to get user choice
        choice = cli_confirm(
            config,
            'Set up shell aliases?',
            ['Yes, set up aliases', 'No, skip this step'],
        )

        if choice == 0:  # User chose "Yes"
            success = add_aliases_to_shell_config()
            if success:
                print_formatted_text('')
                print_formatted_text(
                    HTML('<ansigreen>✅ Aliases added successfully!</ansigreen>')
                )

                # Get the appropriate reload command using the shell config manager
                shell_manager = ShellConfigManager()
                reload_cmd = shell_manager.get_reload_command()

                print_formatted_text(
                    HTML(
                        f'<grey>Run <b>{reload_cmd}</b> (or restart your terminal) to use the new aliases.</grey>'
                    )
                )
            else:
                print_formatted_text('')
                print_formatted_text(
                    HTML(
                        '<ansired>❌ Failed to add aliases. You can set them up manually later.</ansired>'
                    )
                )
        else:  # User chose "No"
            print_formatted_text('')
            print_formatted_text(
                HTML(
                    '<grey>Skipped alias setup. You can run this setup again anytime.</grey>'
                )
            )

    print_formatted_text('')


async def main_with_loop(loop: asyncio.AbstractEventLoop) -> None:
    """Runs the agent in CLI mode."""
    args = parse_arguments()

    # Set log level from command line argument if provided
    if args.log_level and isinstance(args.log_level, str):
        log_level = getattr(logging, str(args.log_level).upper())
        logger.setLevel(log_level)
    else:
        # Set default log level to WARNING if no LOG_LEVEL environment variable is set
        # (command line argument takes precedence over environment variable)
        env_log_level = os.getenv('LOG_LEVEL')
        if not env_log_level:
            logger.setLevel(logging.WARNING)

    # Load config from toml and override with command line arguments
    config: OpenHandsConfig = setup_config_from_args(args)

    # Attempt to install VS Code extension if applicable (one-time attempt)
    attempt_vscode_extension_install()

    # Load settings from Settings Store
    # TODO: Make this generic?
    settings_store = await FileSettingsStore.get_instance(config=config, user_id=None)
    settings = await settings_store.load()

    # Track if we've shown the banner during setup
    banner_shown = False

    # If settings don't exist, automatically enter the setup flow
    if not settings:
        # Clear the terminal before showing the banner
        clear()

        await run_setup_flow(config, settings_store)
        banner_shown = True

        settings = await settings_store.load()

    # Use settings from settings store if available and override with command line arguments
    if settings:
        if args.agent_cls:
            config.default_agent = str(args.agent_cls)
        else:
            # settings.agent is not None because we check for it in setup_config_from_args
            assert settings.agent is not None
            config.default_agent = settings.agent
        if not args.llm_config and settings.llm_model and settings.llm_api_key:
            llm_config = config.get_llm_config()
            llm_config.model = settings.llm_model
            llm_config.api_key = settings.llm_api_key
            llm_config.base_url = settings.llm_base_url
            config.set_llm_config(llm_config)
        config.security.confirmation_mode = (
            settings.confirmation_mode if settings.confirmation_mode else False
        )

        if settings.enable_default_condenser:
            # TODO: Make this generic?
            llm_config = config.get_llm_config()
            agent_config = config.get_agent_config(config.default_agent)
            agent_config.condenser = LLMSummarizingCondenserConfig(
                llm_config=llm_config,
                type='llm',
            )
            config.set_agent_config(agent_config)
            config.enable_default_condenser = True
        else:
            agent_config = config.get_agent_config(config.default_agent)
            agent_config.condenser = NoOpCondenserConfig(type='noop')
            config.set_agent_config(agent_config)
            config.enable_default_condenser = False

    # Determine if CLI defaults should be overridden
    val_override = args.override_cli_mode
    should_override_cli_defaults = (
        val_override is True
        or (isinstance(val_override, str) and val_override.lower() in ('true', '1'))
        or (isinstance(val_override, int) and val_override == 1)
    )

    if not should_override_cli_defaults:
        config.runtime = 'cli'
        if not config.workspace_base:
            config.workspace_base = os.getcwd()
        config.security.confirmation_mode = True

        # Need to finalize config again after setting runtime to 'cli'
        # This ensures Jupyter plugin is disabled for CLI runtime
        finalize_config(config)

    # Check if we should show the alias setup flow
    # Only show it if aliases don't exist in the shell configuration
    # and we're in an interactive environment (not during tests or CI)
    if not aliases_exist_in_shell_config() and sys.stdin.isatty():
        # Clear the terminal if we haven't shown a banner yet
        if not banner_shown:
            clear()

        run_alias_setup_flow(config)
        banner_shown = True

    # TODO: Set working directory from config or use current working directory?
    current_dir = config.workspace_base

    if not current_dir:
        raise ValueError('Workspace base directory not specified')

    if not check_folder_security_agreement(config, current_dir):
        # User rejected, exit application
        return

    # Read task from file, CLI args, or stdin
    if args.file:
        # For CLI usage, we want to enhance the file content with a prompt
        # that instructs the agent to read and understand the file first
        with open(args.file, 'r', encoding='utf-8') as file:
            file_content = file.read()

        # Create a prompt that instructs the agent to read and understand the file first
        task_str = f"""The user has tagged a file '{args.file}'.
Please read and understand the following file content first:

```
{file_content}
```

After reviewing the file, please ask the user what they would like to do with it."""
    else:
        task_str = read_task(args, config.cli_multiline_input)

    # Setup the runtime
    get_runtime_cls(config.runtime).setup(config)

    # Run the first session
    new_session_requested = await run_session(
        loop,
        config,
        settings_store,
        current_dir,
        task_str,
        session_name=args.name,
        skip_banner=banner_shown,
    )

    # If a new session was requested, run it
    while new_session_requested:
        new_session_requested = await run_session(
            loop, config, settings_store, current_dir, None
        )

    # Teardown the runtime
    get_runtime_cls(config.runtime).teardown(config)


def main():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main_with_loop(loop))
    except KeyboardInterrupt:
        print_formatted_text('⚠️ Session was interrupted: interrupted\n')
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


if __name__ == '__main__':
    main()
