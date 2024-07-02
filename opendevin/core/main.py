import asyncio
import os
import signal
import sys
from typing import Callable, Type

import agenthub  # noqa F401 (we import this to get the agents registered)
from opendevin.controller import AgentController
from opendevin.controller.agent import Agent
from opendevin.controller.state.state import State
from opendevin.core.config import args, config, get_llm_config_arg
from opendevin.core.logger import opendevin_logger as logger
from opendevin.core.schema import AgentState
from opendevin.events import EventSource, EventStream, EventStreamSubscriber
from opendevin.events.action import MessageAction
from opendevin.events.event import Event
from opendevin.events.observation import AgentStateChangedObservation
from opendevin.llm.llm import LLM
from opendevin.runtime.sandbox import Sandbox
from opendevin.runtime.server.runtime import ServerRuntime

_is_shutting_down = False


async def shutdown(
    sig: signal.Signals,
    loop: asyncio.AbstractEventLoop,
    shutdown_event: asyncio.Event,
) -> None:
    global _is_shutting_down
    if _is_shutting_down:
        return
    _is_shutting_down = True

    logger.info(f'Received exit signal {sig.name}...')
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    [task.cancel() for task in tasks]
    await asyncio.gather(*tasks, return_exceptions=True)
    shutdown_event.set()
    loop.stop()


def create_signal_handler(
    sig: signal.Signals, loop: asyncio.AbstractEventLoop, shutdown_event: asyncio.Event
) -> Callable[[], None]:
    def handler() -> None:
        asyncio.create_task(shutdown(sig, loop, shutdown_event))

    return handler


def read_task_from_file(file_path: str) -> str:
    """Read task from the specified file."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()


def read_task_from_stdin() -> str:
    """Read task from stdin."""
    return sys.stdin.read()


async def main(
    task_str: str = '',
    exit_on_message: bool = False,
    fake_user_response_fn: Callable[[State | None], str] | None = None,
    sandbox: Sandbox | None = None,
    runtime_tools_config: dict | None = None,
    sid: str | None = None,
) -> State | None:
    """Main coroutine to run the agent controller with task input flexibility.
    It's only used when you launch opendevin backend directly via cmdline.

    Args:
        task_str: The task to run.
        exit_on_message: quit if agent asks for a message from user (optional)
        fake_user_response_fn: An optional function that receives the current state (could be None) and returns a fake user response.
        sandbox: An optional sandbox to run the agent in.
    """

    # Determine the task source
    if task_str:
        task = task_str
    elif args.file:
        task = read_task_from_file(args.file)
    elif args.task:
        task = args.task
    elif not sys.stdin.isatty():
        task = read_task_from_stdin()
    else:
        raise ValueError('No task provided. Please specify a task through -t, -f.')

    # only one of model_name or llm_config is required
    if args.llm_config:
        # --llm_config
        # llm_config can contain any of the attributes of LLMConfig
        llm_config = get_llm_config_arg(args.llm_config)

        if llm_config is None:
            raise ValueError(f'Invalid toml file, cannot read {args.llm_config}')

        logger.info(
            f'Running agent {args.agent_cls} (model: {llm_config.model}, llm_config: {args.llm_config}) with task: "{task}"'
        )

        # create LLM instance with the given config
        llm = LLM(llm_config=llm_config)
    else:
        # --model-name model_name
        logger.info(
            f'Running agent {args.agent_cls} (model: {args.model_name}), with task: "{task}"'
        )
        llm = LLM(args.model_name)

    loop = asyncio.get_running_loop()
    shutdown_event = asyncio.Event()
    signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)
    for sig in signals:
        loop.add_signal_handler(sig, create_signal_handler(sig, loop, shutdown_event))

    # set up the agent
    AgentCls: Type[Agent] = Agent.get_cls(args.agent_cls)
    agent = AgentCls(llm=llm)

    # set up the event stream
    cli_session = 'main' + ('_' + sid if sid else '')
    event_stream = EventStream(cli_session)

    # restore cli session if enabled
    initial_state = None
    if config.enable_cli_session:
        try:
            logger.info('Restoring agent state from cli session')
            initial_state = State.restore_from_session(cli_session)
        except Exception as e:
            print('Error restoring state', e)

    # init controller with this initial state
    controller = AgentController(
        agent=agent,
        max_iterations=args.max_iterations,
        max_budget_per_task=args.max_budget_per_task,
        event_stream=event_stream,
        initial_state=initial_state,
    )

    # runtime and tools
    runtime = ServerRuntime(event_stream=event_stream, sandbox=sandbox)

    try:
        runtime.init_sandbox_plugins(controller.agent.sandbox_plugins)
        runtime.init_runtime_tools(
            controller.agent.runtime_tools,
            is_async=False,
            runtime_tools_config=runtime_tools_config,
        )

        # browser eval specific
        # TODO: move to a better place
        if runtime.browser and runtime.browser.eval_dir:
            logger.info(f'Evaluation directory: {runtime.browser.eval_dir}')
            with open(
                os.path.join(runtime.browser.eval_dir, 'goal.txt'),
                'r',
                encoding='utf-8',
            ) as f:
                task = f.read()
                logger.info(f'Dynamic Eval task: {task}')

        # start event is a MessageAction with the task, either resumed or new
        if config.enable_cli_session and initial_state is not None:
            # we're resuming the previous session
            await event_stream.add_event(
                MessageAction(
                    content="Let's get back on track. If you experienced errors before, do NOT resume your task. Ask me about it."
                ),
                EventSource.USER,
            )
        elif initial_state is None:
            # init with the provided task
            await event_stream.add_event(MessageAction(content=task), EventSource.USER)

        async def on_event(event: Event):
            if isinstance(event, AgentStateChangedObservation):
                if event.agent_state == AgentState.AWAITING_USER_INPUT:
                    if exit_on_message:
                        message = '/exit'
                    elif fake_user_response_fn is None:
                        message = input('Request user input >> ')
                    else:
                        message = fake_user_response_fn(controller.get_state())
                    action = MessageAction(content=message)
                    await event_stream.add_event(action, EventSource.USER)

        event_stream.subscribe(EventStreamSubscriber.MAIN, on_event)

        # Use an event to keep the main coroutine running
        shutdown_event = asyncio.Event()

        while not _is_shutting_down:
            if controller.get_agent_state() in [
                AgentState.FINISHED,
                AgentState.REJECTED,
                AgentState.ERROR,
                AgentState.PAUSED,
                AgentState.STOPPED,
            ]:
                break

            try:
                await asyncio.wait_for(shutdown_event.wait(), timeout=1)
                break  # Exit the loop if shutdown_event is set
            except asyncio.TimeoutError:
                # Timeout occurred, continue the loop
                pass

        # save session when we're about to close
        if config.enable_cli_session:
            end_state = controller.get_state()
            end_state.save_to_session(cli_session)

    except asyncio.CancelledError:
        logger.info('Main task cancelled')
    finally:
        await controller.close()
        runtime.close()
        logger.info('Successfully shut down the OpenDevin server.')
        if not loop.is_closed():
            loop.stop()

    return controller.get_state()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info('Received keyboard interrupt, exiting...')
    finally:
        logger.info('OpenDevin has shut down.')
