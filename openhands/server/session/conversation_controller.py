from openhands.controller.agent import Agent
from openhands.controller.state.state import State
from openhands.core.schema.agent import AgentState
from openhands.server.session.conversation_event_stream import ConversationEventStream


class ConversationController:
    """
    Interface providing forward compatibility between the old AgentController and the new AgentSDK Conversation API.
    """

    def save_state(self):
        raise NotImplementedError()

    def close(self):
        raise NotImplementedError()

    def set_agent_state_to(self, agent_state: AgentState):
        raise NotImplementedError()

    @property
    def agent(self) -> Agent:
        raise NotImplementedError()

    @property
    def state(self) -> State:
        raise NotImplementedError()

    @property
    def event_stream(self) -> ConversationEventStream:
        raise NotImplementedError()
