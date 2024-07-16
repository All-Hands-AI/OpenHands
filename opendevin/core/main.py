import asyncio
import os
import sys
from typing import Callable, Type

import agenthub  # noqa F401 (we import this to get the agents registered)
from opendevin.controller import AgentController
from opendevin.controller.agent import Agent
from opendevin.controller.state.state import State
from opendevin.core.config import config, get_llm_config_arg, parse_arguments
from opendevin.core.logger import opendevin_logger as logger
from opendevin.core.schema import AgentState
from opendevin.events import EventSource, EventStream, EventStreamSubscriber
from opendevin.events.action import MessageAction
from opendevin.events.event import Event
from opendevin.events.observation import AgentStateChangedObservation
from opendevin.llm.llm import LLM
from opendevin.runtime import get_runtime_cls
from opendevin.runtime.sandbox import Sandbox


def read_task_from_file(file_path: str) -> str:
    """Read task from the specified file."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()


def read_task_from_stdin() -> str:
    """Read task from stdin."""
    return sys.stdin.read()


async def run_agent_controller(
    agent: Agent,
    task_str: str,
    max_iterations: int | None = None,
    max_budget_per_task: float | None = None,
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
    # Logging
    logger.info(
        f'Running agent {agent.name}, model {agent.llm.model_name}, with task: "{task_str}"'
    )

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
        max_iterations=max_iterations,
        max_budget_per_task=max_budget_per_task,
        event_stream=event_stream,
        initial_state=initial_state,
    )

    # runtime and tools
    runtime_cls = get_runtime_cls(config.runtime)
    runtime = runtime_cls(event_stream=event_stream, sandbox=sandbox)
    await runtime.ainit()
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
            os.path.join(runtime.browser.eval_dir, 'goal.txt'), 'r', encoding='utf-8'
        ) as f:
            task_str = f.read()
            logger.info(f'Dynamic Eval task: {task_str}')

    # start event is a MessageAction with the task, either resumed or new
    if config.enable_cli_session and initial_state is not None:
        # we're resuming the previous session
        event_stream.add_event(
            MessageAction(
                content="Let's get back on track. If you experienced errors before, do NOT resume your task. Ask me about it."
            ),
            EventSource.USER,
        )
    elif initial_state is None:
        # init with the provided task
        event_stream.add_event(MessageAction(content=task_str), EventSource.USER)

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
                event_stream.add_event(action, EventSource.USER)

    event_stream.subscribe(EventStreamSubscriber.MAIN, on_event)
    while controller.state.agent_state not in [
        AgentState.FINISHED,
        AgentState.REJECTED,
        AgentState.ERROR,
        AgentState.PAUSED,
        AgentState.STOPPED,
    ]:
        await asyncio.sleep(1)  # Give back control for a tick, so the agent can run

    # save session when we're about to close
    if config.enable_cli_session:
        end_state = controller.get_state()
        end_state.save_to_session(cli_session)

    # close when done
    await controller.close()
    await runtime.close()
    return controller.get_state()


if __name__ == '__main__':
    args = parse_arguments()

    # Determine the task
    if args.file:
        task_str = read_task_from_file(args.file)
    elif args.task:
        task_str = args.task
    elif not sys.stdin.isatty():
        task_str = read_task_from_stdin()
    else:
        raise ValueError('No task provided. Please specify a task through -t, -f.')

    # Override default LLM configs ([llm] section in config.toml)
    if args.llm_config:
        llm_config = get_llm_config_arg(args.llm_config)
        if llm_config is None:
            raise ValueError(f'Invalid toml file, cannot read {args.llm_config}')
        config.set_llm_config(llm_config)
    llm = LLM(llm_config=config.get_llm_config_from_agent(args.agent_cls))

    # Create the agent
    AgentCls: Type[Agent] = Agent.get_cls(args.agent_cls)
    agent = AgentCls(llm=llm)

    asyncio.run(
        run_agent_controller(
            agent=agent,
            task_str=task_str,
            max_iterations=args.max_iterations,
            max_budget_per_task=args.max_budget_per_task,
        )
    )
