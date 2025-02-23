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
from openhands.utils.prompt import PromptManager


class Memory:
    """
    Memory is a component that listens to the EventStream for either user MessageAction (to create
    a RecallAction) or a RecallAction (to produce a RecallObservation).
    """

    def __init__(self, event_stream: EventStream, microagents_dir: str):
        self.event_stream = event_stream
        self.microagents_dir = microagents_dir
        # Subscribe to events
        self.event_stream.subscribe(
            EventStreamSubscriber.MEMORY,
            self.on_event,
            'Memory',
        )
        # Load global microagents (Knowledge + Repo).
        self._load_global_microagents()

        # Additional placeholders to store user workspace microagents if needed
        self.repo_microagents: dict[str, RepoMicroAgent] = {}
        self.knowledge_microagents: dict[str, KnowledgeMicroAgent] = {}

    def _load_global_microagents(self) -> None:
        """
        Loads microagents from the global microagents_dir.
        This is effectively what used to happen in PromptManager.
        """
        repo_agents, knowledge_agents, _task_agents = load_microagents_from_dir(
            self.microagents_dir
        )
        for name, agent in knowledge_agents.items():
            if isinstance(agent, KnowledgeMicroAgent):
                self.knowledge_microagents[name] = agent
        for name, agent in repo_agents.items():
            if isinstance(agent, RepoMicroAgent):
                self.repo_microagents[name] = agent

    def on_event(self, event: Event):
        """Handle an event from the event stream."""
        if isinstance(event, MessageAction):
            self.on_user_message_action(event)
        elif isinstance(event, RecallAction):
            self.on_recall_action(event)

    def on_user_message_action(self, event: MessageAction):
        """Replicates old microagent logic: if a microagent triggers on user text,
        we embed it in an <extra_info> block and post a RecallObservation."""
        if event.source != 'user':
            return

        # If there's no text, do nothing
        user_text = event.content.strip()
        if not user_text:
            return
        # Gather all triggered microagents
        microagent_blocks = []
        for name, agent in self.knowledge_microagents.items():
            trigger = agent.match_trigger(user_text)
            if trigger:
                logger.info("Microagent '%s' triggered by keyword '%s'", name, trigger)
                micro_text = (
                    f'<extra_info>\n'
                    f'The following information has been included based on a keyword match for "{trigger}". '
                    f"It may or may not be relevant to the user's request.\n\n"
                    f'{agent.content}\n'
                    f'</extra_info>'
                )
                microagent_blocks.append(micro_text)

        if microagent_blocks:
            # Combine all triggered microagents into a single RecallObservation
            combined_text = '\n'.join(microagent_blocks)
            obs = RecallObservation(content=combined_text)
            self.event_stream.add_event(
                obs, event.source if event.source else EventSource.ENVIRONMENT
            )

    def on_recall_action(self, event: RecallAction):
        """If a RecallAction explicitly arrives, handle it."""
        assert isinstance(event, RecallAction)

        user_query = event.query.get('keywords', [])
        matched_content = self.find_microagent_content(user_query)
        obs = RecallObservation(content=matched_content)
        self.event_stream.add_event(
            obs, event.source if event.source else EventSource.ENVIRONMENT
        )

    def find_microagent_content(self, keywords: list[str]) -> str:
        """Replicate the same microagent logic."""
        matched_texts: list[str] = []
        for name, agent in self.knowledge_microagents.items():
            for kw in keywords:
                trigger = agent.match_trigger(kw)
                if trigger:
                    logger.info(
                        "Microagent '%s' triggered by explicit RecallAction keyword '%s'",
                        name,
                        trigger,
                    )
                    block = (
                        f'<extra_info>\n'
                        f"(via RecallAction) Included knowledge from microagent '{name}', triggered by '{trigger}'\n\n"
                        f'{agent.content}\n'
                        f'</extra_info>'
                    )
                    matched_texts.append(block)
        return '\n'.join(matched_texts)

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
            if isinstance(ma, KnowledgeMicroAgent):
                self.knowledge_microagents[ma.name] = ma
            elif isinstance(ma, RepoMicroAgent):
                self.repo_microagents[ma.name] = ma

    def set_prompt_manager(self, prompt_manager: PromptManager):
        self.prompt_manager = prompt_manager
