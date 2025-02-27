from openhands.core.logger import openhands_logger as logger
from openhands.events.action.agent import RecallAction
from openhands.events.action.message import MessageAction
from openhands.events.event import Event, EventSource
from openhands.events.observation.agent import (
    RecallObservation,
)
from openhands.events.stream import EventStream, EventStreamSubscriber
from openhands.microagent import (
    BaseMicroAgent,
    KnowledgeMicroAgent,
    RepoMicroAgent,
    load_microagents_from_dir,
)
from openhands.utils.prompt import PromptManager, RepositoryInfo, RuntimeInfo


class Memory:
    """
    Memory is a component that listens to the EventStream for either user MessageAction (to create
    a RecallAction) or a RecallAction (to produce a RecallObservation).
    """

    def __init__(
        self,
        event_stream: EventStream,
        microagents_dir: str,
        disabled_microagents: list[str] | None = None,
    ):
        self.event_stream = event_stream
        self.microagents_dir = microagents_dir
        self.disabled_microagents = disabled_microagents or []
        # Subscribe to events
        self.event_stream.subscribe(
            EventStreamSubscriber.MEMORY,
            self.on_event,
            'Memory',
        )

        # Additional placeholders to store user workspace microagents if needed
        self.repo_microagents: dict[str, RepoMicroAgent] = {}
        self.knowledge_microagents: dict[str, KnowledgeMicroAgent] = {}

        # Track whether we've seen the first user message
        self._first_user_message_seen = False

        # Store repository / runtime info to send them to the templating later
        self.repository_info: RepositoryInfo | None = None
        self.runtime_info: RuntimeInfo | None = None

        # Load global microagents (Knowledge + Repo)
        # from typically OpenHands/microagents (i.e., the PUBLIC microagents)
        self._load_global_microagents()

        # TODO: enable_prompt_extensions

    def _load_global_microagents(self) -> None:
        """
        Loads microagents from the global microagents_dir
        This is effectively what used to happen in PromptManager.
        """
        repo_agents, knowledge_agents, _ = load_microagents_from_dir(
            self.microagents_dir
        )
        for name, agent in knowledge_agents.items():
            if name in self.disabled_microagents:
                continue
            if isinstance(agent, KnowledgeMicroAgent):
                self.knowledge_microagents[name] = agent
        for name, agent in repo_agents.items():
            if name in self.disabled_microagents:
                continue
            if isinstance(agent, RepoMicroAgent):
                self.repo_microagents[name] = agent

    def set_repository_info(self, repo_name: str, repo_directory: str) -> None:
        """Store repository info so we can reference it in an observation."""
        self.repository_info = RepositoryInfo(repo_name, repo_directory)
        self.prompt_manager.set_repository_info(self.repository_info)

    def set_runtime_info(self, runtime_hosts: dict[str, int]) -> None:
        """Store runtime info (web hosts, ports, etc.)."""
        # e.g. { '127.0.0.1': 8080 }
        self.runtime_info = RuntimeInfo(available_hosts=runtime_hosts)
        self.prompt_manager.set_runtime_info(self.runtime_info)

    def on_event(self, event: Event):
        """Handle an event from the event stream."""
        if isinstance(event, MessageAction):
            if event.source == 'user':
                # If this is the first user message, create and add a RecallObservation
                # with info about repo and runtime.
                if not self._first_user_message_seen:
                    self._first_user_message_seen = True
                    self._on_first_user_message(event)
                    # continue with the next handler, to include microagents if suitable for this user message
            self._on_user_message_action(event)
        elif isinstance(event, RecallAction):
            self._on_recall_action(event)

    def _on_first_user_message(self, event: MessageAction):
        """Add repository and runtime information to the stream as a RecallObservation."""
        # Collect raw repository instructions
        repo_instructions = ''
        assert (
            len(self.repo_microagents) <= 1
        ), f'Expecting at most one repo microagent, but found {len(self.repo_microagents)}: {self.repo_microagents.keys()}'
        for microagent in self.repo_microagents.values():
            # We assume these are the repo instructions
            if repo_instructions:
                repo_instructions += '\n\n'
            repo_instructions += microagent.content
        
        # Create observation with structured data, not formatted text
        obs_data = {
            "type": "environment_info",
            "repository_info": self.repository_info.model_dump() if self.repository_info else None,
            "runtime_info": self.runtime_info.model_dump() if self.runtime_info else None,
            "repository_instructions": repo_instructions if repo_instructions else None
        }

        # Send structured data in the observation
        obs = RecallObservation(
            content=json.dumps(obs_data)
        )

        self.event_stream.add_event(obs, EventSource.ENVIRONMENT)

    def _on_user_message_action(self, event: MessageAction):
        """When a user message triggers microagents, create a RecallObservation with structured data."""
        if event.source != 'user':
            return
    
        # If there's no text, do nothing
        user_text = event.content.strip()
        if not user_text:
            return
        
        # Gather all triggered microagents
        triggered_agents = []
        for name, agent in self.knowledge_microagents.items():
            trigger = agent.match_trigger(user_text)
            if trigger:
                logger.info("Microagent '%s' triggered by keyword '%s'", name, trigger)
                triggered_agents.append({
                    "name": name,
                    "content": agent.content,
                    "trigger": trigger
                })
    
        if triggered_agents:
            # Create structured data observation
            obs_data = {
                "type": "microagent_knowledge",
                "triggered_agents": triggered_agents
            }
            obs = RecallObservation(content=json.dumps(obs_data))
            self.event_stream.add_event(obs, event.source if event.source else EventSource.ENVIRONMENT)

    def _on_recall_action(self, event: RecallAction):
        """If a RecallAction explicitly arrives, handle it."""
        assert isinstance(event, RecallAction)

        user_query = event.query.get('keywords', [])
        matched_content = ''
        # matched_content = self.find_microagent_content(user_query)
        obs = RecallObservation(content=matched_content)
        self.event_stream.add_event(
            obs, event.source if event.source else EventSource.ENVIRONMENT
        )

    def load_user_workspace_microagents(
        self, user_microagents: list[BaseMicroAgent]
    ) -> None:
        """
        If you want to load microagents from a user's cloned repo or workspace directory,
        call this from agent_session or setup once the workspace is cloned.
        """
        logger.info(
            'Loading user workspace microagents: %s', [m.name for m in user_microagents]
        )
        for ma in user_microagents:
            if ma.name in self.disabled_microagents:
                continue
            if isinstance(ma, KnowledgeMicroAgent):
                self.knowledge_microagents[ma.name] = ma
            elif isinstance(ma, RepoMicroAgent):
                self.repo_microagents[ma.name] = ma

    def set_prompt_manager(self, prompt_manager: PromptManager):
        self.prompt_manager = prompt_manager
