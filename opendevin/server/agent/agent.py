import asyncio
from typing import Dict, List, Optional

from opendevin.controller import AgentController
from opendevin.controller.agent import Agent
from opendevin.core import config
from opendevin.core.logger import opendevin_logger as logger
from opendevin.core.schema import ActionType, ConfigType, TaskState, TaskStateAction
from opendevin.events.action import (
    Action,
    NullAction,
)
from opendevin.events.observation import (
    NullObservation,
    Observation,
    UserMessageObservation,
)
from opendevin.llm.llm import LLM
from opendevin.server.session import session_manager

# new task state to valid old task states
VALID_TASK_STATE_MAP: Dict[TaskStateAction, List[TaskState]] = {
    TaskStateAction.PAUSE: [TaskState.RUNNING],
    TaskStateAction.RESUME: [TaskState.PAUSED],
    TaskStateAction.STOP: [
        TaskState.RUNNING,
        TaskState.PAUSED,
        TaskState.AWAITING_USER_INPUT,
    ],
}
IGNORED_TASK_STATE_MAP: Dict[TaskStateAction, List[TaskState]] = {
    TaskStateAction.PAUSE: [
        TaskState.INIT,
        TaskState.PAUSED,
        TaskState.STOPPED,
        TaskState.FINISHED,
        TaskState.AWAITING_USER_INPUT,
    ],
    TaskStateAction.RESUME: [
        TaskState.INIT,
        TaskState.RUNNING,
        TaskState.STOPPED,
        TaskState.FINISHED,
        TaskState.AWAITING_USER_INPUT,
    ],
    TaskStateAction.STOP: [TaskState.INIT, TaskState.STOPPED, TaskState.FINISHED],
}
TASK_STATE_ACTION_MAP: Dict[TaskStateAction, TaskState] = {
    TaskStateAction.START: TaskState.RUNNING,
    TaskStateAction.PAUSE: TaskState.PAUSED,
    TaskStateAction.RESUME: TaskState.RUNNING,
    TaskStateAction.STOP: TaskState.STOPPED,
}


class AgentUnit:
    """Represents a session with an agent.

    Attributes:
        controller: The AgentController instance for controlling the agent.
        agent_task: The task representing the agent's execution.
    """

    sid: str
    controller: Optional[AgentController] = None
    agent_task: Optional[asyncio.Task] = None

    def __init__(self, sid):
        """Initializes a new instance of the Session class."""
        self.sid = sid

    async def send_error(self, message):
        """Sends an error message to the client.

        Args:
            message: The error message to send.
        """
        await session_manager.send_error(self.sid, message)

    async def send_message(self, message):
        """Sends a message to the client.

        Args:
            message: The message to send.
        """
        await session_manager.send_message(self.sid, message)

    async def send(self, data):
        """Sends data to the client.

        Args:
            data: The data to send.
        """
        await session_manager.send(self.sid, data)

    async def dispatch(self, action: str | None, data: dict):
        """Dispatches actions to the agent from the client."""
        if action is None:
            await self.send_error('Invalid action')
            return

        match action:
            case ActionType.INIT:
                await self.create_controller(data)
            case ActionType.RECONNECT:
                if self.controller is None:
                    await self.create_controller(data)
                    return
                await self.init_done()
            case ActionType.START:
                await self.start_task(data)
            case ActionType.USER_MESSAGE:
                await self.send_user_message(data)
            case ActionType.CHANGE_TASK_STATE:
                task_state_action = data.get('args', {}).get('task_state_action', None)
                if task_state_action is None:
                    await self.send_error('No task state action specified.')
                    return
                await self.set_task_state(TaskStateAction(task_state_action))
            case ActionType.CHAT:
                if self.controller is None:
                    await self.send_error('No agent started. Please wait a second...')
                    return
                self.controller.add_history(
                    NullAction(), UserMessageObservation(data['message'])
                )
            case _:
                await self.send_error("I didn't recognize this action:" + action)

    def get_arg_or_default(self, _args: dict, key: ConfigType) -> str:
        """Gets an argument from the args dictionary or the default value.

        Args:
            _args: The args dictionary.
            key: The key to get.

        Returns:
            The value of the key or the default value.
        """

        return _args.get(key, config.get(key))

    async def create_controller(self, start_event: dict):
        """Creates an AgentController instance.

        Args:
            start_event: The start event data (optional).
        """
        args = {
            key: value
            for key, value in start_event.get('args', {}).items()
            if value != ''
        }  # remove empty values, prevent FE from sending empty strings
        agent_cls = self.get_arg_or_default(args, ConfigType.AGENT)
        model = self.get_arg_or_default(args, ConfigType.LLM_MODEL)
        api_key = self.get_arg_or_default(args, ConfigType.LLM_API_KEY)
        api_base = config.get(ConfigType.LLM_BASE_URL)
        max_iterations = self.get_arg_or_default(args, ConfigType.MAX_ITERATIONS)
        max_chars = self.get_arg_or_default(args, ConfigType.MAX_CHARS)

        logger.info(f'Creating agent {agent_cls} using LLM {model}')
        llm = LLM(model=model, api_key=api_key, base_url=api_base)
        try:
            self.controller = AgentController(
                sid=self.sid,
                agent=Agent.get_cls(agent_cls)(llm),
                max_iterations=int(max_iterations),
                max_chars=int(max_chars),
                callbacks=[self.on_agent_event],
            )
        except Exception as e:
            logger.exception(f'Error creating controller: {e}')
            await self.send_error(
                'Error creating controller. Please check Docker is running and visit `https://opendevin.github.io/OpenDevin/modules/usage/troubleshooting` for more debugging information..'
            )
            return
        await self.init_done()

    async def init_done(self):
        if self.controller is None:
            await self.send_error('No agent started.')
            return
        await self.send(
            {
                'action': ActionType.INIT,
                'message': 'Control loop started.',
            }
        )
        await self.controller.notify_task_state_changed()

    async def start_task(self, start_event):
        """Starts a task for the agent.

        Args:
            start_event: The start event data.
        """
        task = start_event['args']['task']
        if self.controller is None:
            await self.send_error('No agent started. Please wait a second...')
            return
        try:
            if self.agent_task:
                self.agent_task.cancel()
            self.agent_task = asyncio.create_task(
                self.controller.start(task), name='agent start task loop'
            )
        except Exception as e:
            await self.send_error(f'Error during task loop: {e}')

    async def send_user_message(self, data: dict):
        if not self.agent_task or not self.controller:
            await self.send_error('No agent started.')
            return

        await self.controller.add_user_message(
            UserMessageObservation(data['args']['message'])
        )

    async def set_task_state(self, new_state_action: TaskStateAction):
        """Sets the state of the agent task."""
        if self.controller is None:
            await self.send_error('No agent started.')
            return

        cur_state = self.controller.get_task_state()
        new_state = TASK_STATE_ACTION_MAP.get(new_state_action)
        if new_state is None:
            await self.send_error('Invalid task state action.')
            return
        if cur_state in VALID_TASK_STATE_MAP.get(new_state_action, []):
            await self.controller.set_task_state_to(new_state)
        elif cur_state in IGNORED_TASK_STATE_MAP.get(new_state_action, []):
            # notify once again.
            await self.controller.notify_task_state_changed()
            return
        else:
            await self.send_error('Current task state not recognized.')
            return

        if new_state_action == TaskStateAction.RESUME:
            if self.agent_task:
                self.agent_task.cancel()
            self.agent_task = asyncio.create_task(
                self.controller.resume(), name='agent resume task loop'
            )

    async def on_agent_event(self, event: Observation | Action):
        """Callback function for agent events.

        Args:
            event: The agent event (Observation or Action).
        """
        if isinstance(event, NullAction):
            return
        if isinstance(event, NullObservation):
            return
        await self.send(event.to_dict())

    def close(self):
        if self.agent_task:
            self.agent_task.cancel()
        if self.controller is not None:
            self.controller.action_manager.sandbox.close()
