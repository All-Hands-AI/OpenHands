import asyncio
import os
from typing import Optional

from opendevin import config
from opendevin.action import (
    Action,
    NullAction,
)
from opendevin.agent import Agent
from opendevin.controller import AgentController
from opendevin.llm.llm import LLM
from opendevin.logging import opendevin_logger as logger
from opendevin.observation import NullObservation, Observation, UserMessageObservation
from opendevin.schema import ActionType, ConfigType
from opendevin.server.session import session_manager


class AgentManager:
    """Represents a session with an agent.

    Attributes:
        controller: The AgentController instance for controlling the agent.
        agent: The Agent instance representing the agent.
        agent_task: The task representing the agent's execution.
    """

    sid: str

    def __init__(self, sid):
        """Initializes a new instance of the Session class."""
        self.sid = sid
        self.controller: Optional[AgentController] = None
        self.agent: Optional[Agent] = None
        self.agent_task = None

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

        if action == ActionType.INIT:
            await self.create_controller(data)
        elif action == ActionType.START:
            await self.start_task(data)
        else:
            if self.controller is None:
                await self.send_error('No agent started. Please wait a second...')
            elif action == ActionType.CHAT:
                self.controller.add_history(
                    NullAction(), UserMessageObservation(data['message'])
                )
            else:
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
        directory = self.get_arg_or_default(args, ConfigType.WORKSPACE_DIR)
        agent_cls = self.get_arg_or_default(args, ConfigType.AGENT)
        model = self.get_arg_or_default(args, ConfigType.LLM_MODEL)
        api_key = self.get_arg_or_default(args, ConfigType.LLM_API_KEY)
        api_base = self.get_arg_or_default(args, ConfigType.LLM_BASE_URL)
        container_image = self.get_arg_or_default(
            args, ConfigType.SANDBOX_CONTAINER_IMAGE
        )
        max_iterations = self.get_arg_or_default(
            args, ConfigType.MAX_ITERATIONS)

        if not os.path.exists(directory):
            logger.info(
                'Workspace directory %s does not exist. Creating it...', directory
            )
            os.makedirs(directory)
        directory = os.path.relpath(directory, os.getcwd())
        llm = LLM(model=model, api_key=api_key, base_url=api_base)
        AgentCls = Agent.get_cls(agent_cls)
        self.agent = AgentCls(llm)
        try:
            self.controller = AgentController(
                id=self.sid,
                agent=self.agent,
                workdir=directory,
                max_iterations=int(max_iterations),
                container_image=container_image,
                callbacks=[self.on_agent_event],
            )
        except Exception:
            logger.exception('Error creating controller.')
            await self.send_error(
                'Error creating controller. Please check Docker is running using `docker ps`.'
            )
            return
        await self.send({'action': ActionType.INIT, 'message': 'Control loop started.'})

    async def start_task(self, start_event):
        """Starts a task for the agent.

        Args:
            start_event: The start event data.
        """
        if 'task' not in start_event['args']:
            await self.send_error('No task specified')
            return
        await self.send_message('Starting new task...')
        task = start_event['args']['task']
        if self.controller is None:
            await self.send_error('No agent started. Please wait a second...')
            return
        try:
            self.agent_task = await asyncio.create_task(
                self.controller.start_loop(task), name='agent loop'
            )
        except Exception:
            await self.send_error('Error during task loop.')

    def on_agent_event(self, event: Observation | Action):
        """Callback function for agent events.

        Args:
            event: The agent event (Observation or Action).
        """
        if isinstance(event, NullAction):
            return
        if isinstance(event, NullObservation):
            return
        event_dict = event.to_dict()
        asyncio.create_task(self.send(event_dict),
                            name='send event in callback')

    def disconnect(self):
        self.websocket = None
        if self.agent_task:
            self.agent_task.cancel()
        if self.controller is not None:
            self.controller.command_manager.shell.close()
