import uuid

from openhands.controller.agent_controller import AgentController
from openhands.core.config.openhands_config import OpenHandsConfig
from openhands.core.conversation import Conversation
from openhands.core.setup import create_agent, create_runtime
from openhands.events.stream import EventStream
from openhands.llm.llm import LLM
from openhands.storage import get_file_store


class OpenHands:
    """Main class for creating and managing OpenHands conversations.

    This class is responsible for creating new conversations based on the provided
    configuration. It serves as the primary entry point for interacting with the
    OpenHands system.

    Attributes:
        config: Configuration for the OpenHands system
    """

    def __init__(self, config: OpenHandsConfig):
        """Initialize the OpenHands instance with the provided configuration.

        Args:
            config: Configuration for the OpenHands system
        """
        self.config = config

    def create_conversation(self, conversation_id: str | None = None) -> Conversation:
        """Create a new conversation with all necessary components.

        This method creates a Runtime, LLM, EventStream, and AgentController according
        to the configuration provided to the constructor, and returns a Conversation
        object containing all these components.

        Args:
            conversation_id: Optional identifier for the conversation. If not provided,
                a unique ID will be generated.

        Returns:
            A Conversation object containing all the components needed for interaction.
        """
        # Create a runtime based on the configuration
        runtime = create_runtime(self.config)

        # Create a file store
        file_store = get_file_store(self.config.file_store, self.config.file_store_path)

        # Create an event stream for the conversation
        # Generate a unique ID if none is provided
        sid = (
            conversation_id
            if conversation_id is not None
            else f'conversation-{uuid.uuid4()}'
        )
        event_stream = EventStream(sid=sid, file_store=file_store)

        # Get the default LLM configuration and create an LLM instance
        llm_config = self.config.get_llm_config()
        llm = LLM(llm_config)

        # Create an agent using the factory function
        agent = create_agent(self.config)

        # Create an agent controller
        agent_controller = AgentController(
            agent=agent,
            event_stream=event_stream,
            max_iterations=self.config.max_iterations,
            max_budget_per_task=self.config.max_budget_per_task,
            agent_to_llm_config=self.config.get_agent_to_llm_config_map(),
            agent_configs=self.config.get_agent_configs(),
            sid=conversation_id,
        )

        # Create and return a Conversation object
        return Conversation(
            conversation_id=conversation_id or event_stream.sid,
            runtime=runtime,
            llm=llm,
            event_stream=event_stream,
            agent_controller=agent_controller,
        )
