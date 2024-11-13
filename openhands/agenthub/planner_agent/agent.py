from openhands.agenthub.planner_agent.prompt import get_prompt_and_images
from openhands.agenthub.planner_agent.response_parser import PlannerResponseParser
from openhands.controller.agent import Agent
from openhands.controller.state.state import State
from openhands.core.config import AgentConfig
from openhands.core.message import ImageContent, Message, TextContent
from openhands.events.action import Action, AgentFinishAction
from openhands.llm.llm import LLM


class PlannerAgent(Agent):
    VERSION = '1.0'
    """
    The planner agent utilizes a special prompting strategy to create long term plans for solving problems.
    The agent is given its previous action-observation pairs, current task, and hint based on last action taken at every step.
    """
    response_parser = PlannerResponseParser()

    def __init__(self, llm: LLM, config: AgentConfig):
        """Initialize the Planner Agent with an LLM

        Parameters:
        - llm (LLM): The llm to be used by this agent
        """
        super().__init__(llm, config)

    def step(self, state: State) -> Action:
        """Checks to see if current step is completed, returns AgentFinishAction if True.
        Otherwise, creates a plan prompt and sends to model for inference, returning the result as the next action.

        Parameters:
        - state (State): The current state given the previous actions and observations

        Returns:
        - AgentFinishAction: If the last state was 'completed', 'verified', or 'abandoned'
        - Action: The next action to take based on llm response
        """
        if state.root_task.state in [
            'completed',
            'verified',
            'abandoned',
        ]:
            return AgentFinishAction()

        prompt, image_urls = get_prompt_and_images(
            state, self.llm.config.max_message_chars
        )
        content = [TextContent(text=prompt)]
        if self.llm.vision_is_active() and image_urls:
            content.append(ImageContent(image_urls=image_urls))
        message = Message(role='user', content=content)
        resp = self.llm.completion(messages=self.llm.format_messages_for_llm(message))
        return self.response_parser.parse(resp)
