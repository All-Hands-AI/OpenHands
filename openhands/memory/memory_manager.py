from openhands.events.action.agent import RecallAction
from openhands.events.action.message import MessageAction
from openhands.events.event import Event, EventSource
from openhands.events.observation.agent import RecallObservation
from openhands.events.stream import EventStream, EventStreamSubscriber


class MemoryManager:
    """
    MemoryManager listens to the EventStream for either user MessageAction (to create
    a RecallAction) or a RecallAction (to produce a RecallObservation).
    """

    def __init__(self, event_stream: EventStream, microagents_dir: str):
        self.event_stream = event_stream
        self.microagents_dir = microagents_dir
        # subscribe to events
        self.event_stream.subscribe(
            EventStreamSubscriber.MAIN,
            self.on_event,
            'MemorySubscriber',
        )
        # Optionally load microagents up front
        # e.g.:
        # repo_microagents, knowledge_microagents, _ = load_microagents_from_dir(microagents_dir)
        # self.knowledge_microagents: dict[str, KnowledgeMicroAgent] = knowledge_microagents

    def on_event(self, event: Event):
        """Handle an event from the event stream."""
        if isinstance(event, MessageAction):
            self.on_user_message_action(event)
        elif isinstance(event, RecallAction):
            self.on_recall_action(event)

    def on_user_message_action(self, event: Event):
        """Check if the user message triggers a recall."""
        if not isinstance(event, MessageAction):
            return
        if event.source != 'user':
            return

        user_text = event.content.lower()
        # Suppose we just define 'github' or 'docker' as triggers, for example:
        triggers = ['github', 'docker', 'repo', 'microagent']
        matched = [kw for kw in triggers if kw in user_text]
        if matched:
            recall = RecallAction(query={'keywords': matched})
            self.event_stream.add_event(recall, event.source)

    def on_recall_action(self, event: Event):
        if not isinstance(event, RecallAction):
            return

        user_query = event.query.get('keywords', [])
        matched_content = self.find_microagent_content(user_query)
        obs = RecallObservation(content=matched_content)
        self.event_stream.add_event(
            obs, event.source if event.source else EventSource.ENVIRONMENT
        )

    def find_microagent_content(self, keywords: list[str]) -> str:
        """For each knowledge microagent, if it has a matching trigger
        for any of these keywords, gather its content.
        """
        matched_texts: list[str] = []

        # Example approach:
        # for agent in self.knowledge_microagents.values():
        #     for kw in keywords:
        #         # Using agent.match_trigger(...) from KnowledgeMicroAgent
        #         trigger = agent.match_trigger(kw)
        #         if trigger:
        #             micro_text = (
        #                 f"<extra_info>\nIncluded knowledge from microagent '{agent.name}' "
        #                 f"triggered by keyword '{trigger}'\n\n{agent.content}\n</extra_info>"
        #             )
        #             matched_texts.append(micro_text)
        return '\n'.join(matched_texts)
