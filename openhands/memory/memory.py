from openhands.core.logger import openhands_logger as logger
from openhands.events.action.agent import RecallAction
from openhands.events.action.message import MessageAction
from openhands.events.event import Event, EventSource
from openhands.events.observation.agent import (
    RecallObservation,
)
from openhands.events.stream import EventStream, EventStreamSubscriber
from openhands.microagent import KnowledgeMicroAgent, load_microagents_from_dir


class MemoryManager:
    """
    MemoryManager listens to the EventStream for either user MessageAction (to create
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
        # Load any knowledge microagents from the given directory
        # If your directory is empty or none found, self.knowledge_microagents is just {}
        _repo_agents, knowledge_agents, _task_agents = load_microagents_from_dir(
            self.microagents_dir
        )
        # We assume knowledge_agents is a dict[str, KnowledgeMicroAgent]
        self.knowledge_microagents: dict[str, KnowledgeMicroAgent] = knowledge_agents

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
