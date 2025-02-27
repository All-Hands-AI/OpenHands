from openhands.core.logger import openhands_logger as logger
from openhands.core.message import Message, TextContent
from openhands.events.event import Event, EventSource
from openhands.events.action.message import MessageAction
from openhands.events.stream import EventStream, EventStreamSubscriber
from openhands.microagent import (
    BaseMicroAgent,
    KnowledgeMicroAgent,
    RepoMicroAgent,
    load_microagents_from_dir,
)
from openhands.utils.prompt import PromptManager, RepositoryInfo, RuntimeInfo


class ConversationMemory:
    """
    ConversationMemory is a component that listens to the EventStream for user MessageAction
    and enhances them with additional context from microagents.
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
            'ConversationMemory',
        )
        # Load global microagents (Knowledge + Repo).
        self._load_global_microagents()

        # Additional placeholders to store user workspace microagents if needed
        self.repo_microagents: dict[str, RepoMicroAgent] = {}
        self.knowledge_microagents: dict[str, KnowledgeMicroAgent] = {}

        # Track whether we've seen the first user message
        self._first_user_message_seen = False

        # Store repository / runtime info to send them to the templating later
        self.repository_info: RepositoryInfo | None = None
        self.runtime_info: RuntimeInfo | None = None

    def _load_global_microagents(self) -> None:
        """
        Loads microagents from the global microagents_dir.
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
                # If this is the first user message, add repository and runtime info
                if not self._first_user_message_seen:
                    self._first_user_message_seen = True
                    self._on_first_user_message(event)
                # Enhance the message with microagent content
                self._on_user_message_action(event)

    def _on_first_user_message(self, event: MessageAction):
        """Add repository and runtime info to the first user message."""
        # Convert MessageAction to Message for compatibility with existing code
        message = Message(role='user', content=[TextContent(text=event.content)])
        
        # Build the repository instructions
        repo_instructions = ''
        assert (
            len(self.repo_microagents) <= 1
        ), f'Expecting at most one repo microagent, but found {len(self.repo_microagents)}: {self.repo_microagents.keys()}'
        for microagent in self.repo_microagents.values():
            # We assume these are the repo instructions
            if repo_instructions:
                repo_instructions += '\n\n'
            repo_instructions += microagent.content

        # Add the info to the message
        self.prompt_manager.add_info_to_initial_message(message)
        
        # Update the original event content
        if message.content and len(message.content) > 1:
            # Combine all TextContent into a single string
            combined_text = ""
            for content in message.content:
                if isinstance(content, TextContent):
                    combined_text += content.text + "\n"
            event.content = combined_text.strip()

    def _on_user_message_action(self, event: MessageAction):
        """Enhance user message with microagent content."""
        if event.source != 'user':
            return

        # If there's no text, do nothing
        user_text = event.content.strip()
        if not user_text:
            return
            
        # Convert MessageAction to Message for compatibility with existing code
        message = Message(role='user', content=[TextContent(text=user_text)])
        
        # Enhance the message with microagent content
        self.enhance_message(message)
        
        # Update the original event content if it was enhanced
        if len(message.content) > 1:
            # Combine all TextContent into a single string
            combined_text = ""
            for content in message.content:
                if isinstance(content, TextContent):
                    combined_text += content.text + "\n"
            event.content = combined_text.strip()

    def enhance_message(self, message: Message) -> None:
        """Enhance the user message with additional context.

        This method is used to enhance the user message with additional context
        about the user's task. The additional context will convert the current
        generic agent into a more specialized agent that is tailored to the user's task.
        """
        if not message.content:
            return

        # if there were other texts included, they were before the user message
        # so the last TextContent is the user message
        # content can be a list of TextContent or ImageContent
        message_content = ''
        for content in reversed(message.content):
            if isinstance(content, TextContent):
                message_content = content.text
                break

        if not message_content:
            return

        for microagent in self.knowledge_microagents.values():
            trigger = microagent.match_trigger(message_content)
            if trigger:
                logger.info(
                    "Microagent '%s' triggered by keyword '%s'",
                    microagent.name,
                    trigger,
                )
                micro_text = f'<extra_info>\nThe following information has been included based on a keyword match for "{trigger}". It may or may not be relevant to the user\'s request.'
                micro_text += '\n\n' + microagent.content
                micro_text += '\n</extra_info>'
                message.content.append(TextContent(text=micro_text))

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