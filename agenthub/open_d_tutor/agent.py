# agenthub/open_d_tutor/agent.py

from opendevin.controller.agent import Agent
from opendevin.controller.state.state import State
from opendevin.events.action import Action, MessageAction
from opendevin.events.observation import Observation
from opendevin.llm.llm import LLM

class OpenDTutorAgent(Agent):
    VERSION = '1.0'
    """
    The Open-D-Tutor Agent provides detailed explanations of the source code for any project.
    """

    def __init__(self, llm: LLM):
        """Initializes the Open-D-Tutor Agent with an llm.

        Parameters:
        - llm (LLM): The llm to be used by this agent
        """
        super().__init__(llm)
        self.reset()

    def step(self, state: State) -> Action:
        """Performs one step using the Open-D-Tutor Agent.
        This includes gathering info on previous steps and prompting the model to provide explanations.

        Parameters:
        - state (State): used to get updated info

        Returns:
        - MessageAction(content) - Message action to provide explanations
        """
        # prepare what we want to send to the LLM
        messages: list[dict[str, str]] = self._get_messages(state)

        response = self.llm.completion(
            messages=messages,
            stop=None,
            temperature=0.0,
        )
        return MessageAction(content=response)

    def _get_messages(self, state: State) -> list[dict[str, str]]:
        messages = [
            {'role': 'system', 'content': "You are an educational assistant. Explain the code and answer questions."},
        ]

        for event in state.history.get_events():
            if isinstance(event, Action):
                messages.append({'role': 'user', 'content': event.content})
            elif isinstance(event, Observation):
                messages.append({'role': 'assistant', 'content': event.content})

        return messages

    def reset(self) -> None:
        """Resets the Open-D-Tutor Agent."""
        super().reset()