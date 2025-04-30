import asyncio
import logging
import sys
from uuid import uuid4

from prompt_toolkit.shortcuts import clear

import openhands.agenthub  # noqa F401 (we import this to get the agents registered)
from openhands.controller import AgentController
from openhands.controller.agent import Agent
from openhands.core.cli_commands import (
    check_folder_security_agreement,
    handle_commands,
)
from openhands.core.cli_tui import (
    UsageMetrics,
    display_banner,
    display_event,
    display_initial_user_prompt,
    display_initialization_animation,
    display_runtime_initialization_message,
    display_welcome_message,
    read_confirmation_input,
    read_prompt_input,
)
from openhands.core.cli_utils import (
    update_usage_metrics,
)
from openhands.core.config import (
    AppConfig,
    parse_arguments,
    setup_config_from_args,
)
from openhands.core.config.condenser_config import NoOpCondenserConfig
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
    ChangeAgentStateAction,
    MessageAction,
)
from openhands.events.event import Event
from openhands.events.observation import (
    AgentStateChangedObservation,
)
from openhands.io import read_task
from openhands.mcp import fetch_mcp_tools_from_config
from openhands.memory.condenser.impl.llm_summarizing_condenser import (
    LLMSummarizingCondenserConfig,
)
from openhands.microagent.microagent import BaseMicroagent
from openhands.runtime.base import Runtime
from openhands.storage.settings.file_settings_store import FileSettingsStore


async def cleanup_session(
    loop: asyncio.AbstractEventLoop,
    agent: Agent,
    runtime: Runtime,
    controller: AgentController,
):
    """Clean up all resources from the current session."""
    try:
        # Cancel all running tasks except the current one
        current_task = asyncio.current_task(loop)
        pending = [task for task in asyncio.all_tasks(loop) if task is not current_task]
        for task in pending:
            task.cancel()

        # Wait for all tasks to complete with a timeout
        if pending:
            await asyncio.wait(pending, timeout=5.0)

        # Reset agent, close runtime and controller
        agent.reset()
        runtime.close()
        await controller.close()
    except Exception as e:
        logger.error(f'Error during session cleanup: {e}')


async def run_session(
    loop: asyncio.AbstractEventLoop,
    config: AppConfig,
    settings_store: FileSettingsStore,
    current_dir: str,
    initial_user_action: str | None = None,
) -> bool:
    reload_microagents = False
    new_session_requested = False

    sid = str(uuid4())
    is_loaded = asyncio.Event()

    # Show runtime initialization message
    display_runtime_initialization_message(config.runtime)

    # Show Initialization loader
    loop.run_in_executor(
        None, display_initialization_animation, 'Initializing...', is_loaded
    )

    agent = create_agent(config)
    mcp_tools = await fetch_mcp_tools_from_config(config.mcp)
    agent.set_mcp_tools(mcp_tools)
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
        nonlocal reload_microagents, new_session_requested
        while True:
            next_message = await read_prompt_input(config.cli_multiline_input)

            if not next_message.strip():
                continue

            (
                close_repl,
                reload_microagents,
                new_session_requested,
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
        nonlocal reload_microagents
        display_event(event, config)
        update_usage_metrics(event, usage_metrics)

        if isinstance(event, AgentStateChangedObservation):
            if event.agent_state in [
                AgentState.AWAITING_USER_INPUT,
                AgentState.FINISHED,
            ]:
                # Reload microagents after initialization of repo.md
                if reload_microagents:
                    microagents: list[BaseMicroagent] = (
                        runtime.get_microagents_from_selected_repo(None)
                    )
                    memory.load_user_workspace_microagents(microagents)
                    reload_microagents = False
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

    # Clear loading animation
    is_loaded.set()

    # Clear the terminal
    clear()

    # Show OpenHands banner and session ID
    display_banner(session_id=sid, is_loaded=is_loaded)

    # Show OpenHands welcome
    display_welcome_message()

    if initial_user_action:
        # If there's an initial user action, enqueue it and do not prompt again
        display_initial_user_prompt(initial_user_action)
        event_stream.add_event(
            MessageAction(content=initial_user_action), EventSource.USER
        )
    else:
        # Otherwise prompt for the user's first message right away
        asyncio.create_task(prompt_for_next_task())

    await run_agent_until_done(
        controller, runtime, memory, [AgentState.STOPPED, AgentState.ERROR]
    )

    await cleanup_session(loop, agent, runtime, controller)

    return new_session_requested


async def main(loop: asyncio.AbstractEventLoop):
    """Runs the agent in CLI mode."""

    args = parse_arguments()

    logger.setLevel(logging.WARNING)

    # Load config from toml and override with command line arguments
    config: AppConfig = setup_config_from_args(args)

    # Load settings from Settings Store
    # TODO: Make this generic?
    settings_store = await FileSettingsStore.get_instance(config=config, user_id=None)
    settings = await settings_store.load()

    # Use settings from settings store if available and override with command line arguments
    if settings:
        config.default_agent = args.agent_cls if args.agent_cls else settings.agent
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

    # TODO: Set working directory from config or use current working directory?
    current_dir = config.workspace_base

    if not current_dir:
        raise ValueError('Workspace base directory not specified')

    if not check_folder_security_agreement(config, current_dir):
        # User rejected, exit application
        return

    # Read task from file, CLI args, or stdin
    task_str = read_task(args, config.cli_multiline_input)

    # Run the first session
    new_session_requested = await run_session(
        loop, config, settings_store, current_dir, task_str
    )

    # If a new session was requested, run it
    while new_session_requested:
        new_session_requested = await run_session(
            loop, config, settings_store, current_dir, None
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
