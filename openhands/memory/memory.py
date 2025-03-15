import asyncio
import os
import uuid
from typing import Callable

import openhands
from openhands.core.logger import openhands_logger as logger
from openhands.events.action.agent import RecallAction
from openhands.events.event import Event, EventSource, RecallType
from openhands.events.observation.agent import (
    MicroagentKnowledge,
    MicroagentObservation,
)
from openhands.events.observation.empty import NullObservation
from openhands.events.stream import EventStream, EventStreamSubscriber
from openhands.microagent import (
    BaseMicroAgent,
    KnowledgeMicroAgent,
    RepoMicroAgent,
    load_microagents_from_dir,
)
from openhands.runtime.base import Runtime
from openhands.utils.prompt import RepositoryInfo, RuntimeInfo

GLOBAL_MICROAGENTS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(openhands.__file__)),
    'microagents',
)


class Memory:
    """
    Memory is a component that listens to the EventStream for information retrieval actions
    (a RecallAction) and publishes observations with the content (such as MicroagentObservation).
    """

    sid: str
    event_stream: EventStream
    status_callback: Callable | None
    loop: asyncio.AbstractEventLoop | None

    def __init__(
        self,
        event_stream: EventStream,
        sid: str,
        status_callback: Callable | None = None,
    ):
        self.event_stream = event_stream
        self.sid = sid if sid else str(uuid.uuid4())
        self.status_callback = status_callback
        self.loop = None

        self.event_stream.subscribe(
            EventStreamSubscriber.MEMORY,
            self.on_event,
            self.sid,
        )

        # Additional placeholders to store user workspace microagents
        self.repo_microagents: dict[str, RepoMicroAgent] = {}
        self.knowledge_microagents: dict[str, KnowledgeMicroAgent] = {}

        # Store repository / runtime info to send them to the templating later
        self.repository_info: RepositoryInfo | None = None
        self.runtime_info: RuntimeInfo | None = None

        # Load global microagents (Knowledge + Repo)
        # from typically OpenHands/microagents (i.e., the PUBLIC microagents)
        self._load_global_microagents()

    def on_event(self, event: Event):
        """Handle an event from the event stream."""
        asyncio.get_event_loop().run_until_complete(self._on_event(event))

    async def _on_event(self, event: Event):
        """Handle an event from the event stream asynchronously."""
        try:
            observation: MicroagentObservation | NullObservation | None = None

            if isinstance(event, RecallAction):
                # if this is a workspace context recall (on first user message)
                # create and add a MicroagentObservation
                # with info about repo and runtime.
                if (
                    event.source == EventSource.USER
                    and event.recall_type == RecallType.WORKSPACE_CONTEXT
                ):
                    observation = self._on_first_microagent_action(event)

                # continue with the next handler, to include knowledge microagents if suitable for this query
                assert observation is None or isinstance(
                    observation, MicroagentObservation
                ), f'Expected a MicroagentObservation, but got {type(observation)}'
                observation = self._on_microagent_action(
                    event, prev_observation=observation
                )

                if observation is None:
                    observation = NullObservation(content='')

                # important: this will release the execution flow from waiting for the retrieval to complete
                observation._cause = event.id  # type: ignore[union-attr]

                self.event_stream.add_event(observation, EventSource.ENVIRONMENT)
        except Exception as e:
            error_str = f'Error: {str(e.__class__.__name__)}'
            logger.error(error_str)
            self.send_error_message('STATUS$ERROR_MEMORY', error_str)
            return

    def _on_first_microagent_action(
        self, event: RecallAction
    ) -> MicroagentObservation | None:
        """Add repository and runtime information to the stream as a MicroagentObservation."""

        # Create ENVIRONMENT info:
        # - repository_info
        # - runtime_info
        # - repository_instructions

        # Collect raw repository instructions
        repo_instructions = ''
        assert (
            len(self.repo_microagents) <= 1
        ), f'Expecting at most one repo microagent, but found {len(self.repo_microagents)}: {self.repo_microagents.keys()}'

        # Retrieve the context of repo instructions
        for microagent in self.repo_microagents.values():
            if repo_instructions:
                repo_instructions += '\n\n'
            repo_instructions += microagent.content

        # Create observation if we have anything
        if self.repository_info or self.runtime_info or repo_instructions:
            obs = MicroagentObservation(
                recall_type=RecallType.WORKSPACE_CONTEXT,
                repo_name=self.repository_info.repo_name
                if self.repository_info and self.repository_info.repo_name is not None
                else '',
                repo_directory=self.repository_info.repo_directory
                if self.repository_info
                and self.repository_info.repo_directory is not None
                else '',
                repo_instructions=repo_instructions if repo_instructions else '',
                runtime_hosts=self.runtime_info.available_hosts
                if self.runtime_info and self.runtime_info.available_hosts is not None
                else {},
                additional_agent_instructions=self.runtime_info.additional_agent_instructions
                if self.runtime_info
                and self.runtime_info.additional_agent_instructions is not None
                else '',
                microagent_knowledge=[],
                content='Retrieved environment info',
            )
            return obs
        return None

    def _on_microagent_action(
        self,
        event: RecallAction,
        prev_observation: MicroagentObservation | None = None,
    ) -> MicroagentObservation | None:
        """When a microagent action triggers microagents, create a MicroagentObservation with structured data."""
        # If there's no query, do nothing
        query = event.query.strip()
        if not query:
            return prev_observation

        assert prev_observation is None or isinstance(
            prev_observation, MicroagentObservation
        ), f'Expected a MicroagentObservation, but got {type(prev_observation)}'

        # Process text to find suitable microagents and create a MicroagentObservation.
        recalled_content: list[MicroagentKnowledge] = []
        for name, microagent in self.knowledge_microagents.items():
            trigger = microagent.match_trigger(query)
            if trigger:
                logger.info("Microagent '%s' triggered by keyword '%s'", name, trigger)
                recalled_content.append(
                    MicroagentKnowledge(
                        name=microagent.name,
                        trigger=trigger,
                        content=microagent.content,
                    )
                )

        if recalled_content:
            if prev_observation is not None:
                # it may be on the first user message that already found some repo info etc
                prev_observation.microagent_knowledge.extend(recalled_content)
            else:
                # if it's not the first user message, we may not have found any information this step
                obs = MicroagentObservation(
                    recall_type=RecallType.KNOWLEDGE,
                    microagent_knowledge=recalled_content,
                    content='Retrieved knowledge from microagents',
                )

                return obs

        return prev_observation

    def load_user_workspace_microagents(
        self, user_microagents: list[BaseMicroAgent]
    ) -> None:
        """
        This method loads microagents from a user's cloned repo or workspace directory.

        This is typically called from agent_session or setup once the workspace is cloned.
        """
        logger.info(
            'Loading user workspace microagents: %s', [m.name for m in user_microagents]
        )
        for user_microagent in user_microagents:
            if isinstance(user_microagent, KnowledgeMicroAgent):
                self.knowledge_microagents[user_microagent.name] = user_microagent
            elif isinstance(user_microagent, RepoMicroAgent):
                self.repo_microagents[user_microagent.name] = user_microagent

    def _load_global_microagents(self) -> None:
        """
        Loads microagents from the global microagents_dir
        """
        repo_agents, knowledge_agents, _ = load_microagents_from_dir(
            GLOBAL_MICROAGENTS_DIR
        )
        for name, agent in knowledge_agents.items():
            if isinstance(agent, KnowledgeMicroAgent):
                self.knowledge_microagents[name] = agent
        for name, agent in repo_agents.items():
            if isinstance(agent, RepoMicroAgent):
                self.repo_microagents[name] = agent

    def set_repository_info(self, repo_name: str, repo_directory: str) -> None:
        """Store repository info so we can reference it in an observation."""
        if repo_name or repo_directory:
            self.repository_info = RepositoryInfo(repo_name, repo_directory)
        else:
            self.repository_info = None

    def set_runtime_info(self, runtime: Runtime) -> None:
        """Store runtime info (web hosts, ports, etc.)."""
        # e.g. { '127.0.0.1': 8080 }
        if runtime.web_hosts or runtime.additional_agent_instructions:
            self.runtime_info = RuntimeInfo(
                available_hosts=runtime.web_hosts,
                additional_agent_instructions=runtime.additional_agent_instructions,
            )
        else:
            self.runtime_info = None

    def send_error_message(self, message_id: str, message: str):
        """Sends an error message if the callback function was provided."""
        if self.status_callback:
            try:
                if self.loop is None:
                    self.loop = asyncio.get_running_loop()
                asyncio.run_coroutine_threadsafe(
                    self._send_status_message('error', message_id, message), self.loop
                )
            except RuntimeError as e:
                logger.error(
                    f'Error sending status message: {e.__class__.__name__}',
                    stack_info=False,
                )

    async def _send_status_message(self, msg_type: str, id: str, message: str):
        """Sends a status message to the client."""
        if self.status_callback:
            self.status_callback(msg_type, id, message)
