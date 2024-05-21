from opendevin.controller.agent import Agent
from opendevin.controller.state.state import State
from opendevin.events.action import Action, AgentDelegateAction, AgentFinishAction
from opendevin.events.observation import AgentDelegateObservation
from opendevin.llm.llm import LLM


class DelegatorAgent(Agent):
    VERSION = '1.0'
    """
    The planner agent utilizes a special prompting strategy to create long term plans for solving problems.
    The agent is given its previous action-observation pairs, current task, and hint based on last action taken at every step.
    """

    current_delegate: str = ''

    def __init__(self, llm: LLM):
        """
        Initialize the Delegator Agent with an LLM

        Parameters:
        - llm (LLM): The llm to be used by this agent
        """
        super().__init__(llm)

    def step(self, state: State) -> Action:
        """
        Checks to see if current step is completed, returns AgentFinishAction if True.
        Otherwise, creates a plan prompt and sends to model for inference, returning the result as the next action.

        Parameters:
        - state (State): The current state given the previous actions and observations

        Returns:
        - AgentFinishAction: If the last state was 'completed', 'verified', or 'abandoned'
        - Action: The next action to take based on llm response
        """
        if self.current_delegate == '':
            self.current_delegate = 'study'
            task = state.get_current_user_intent()
            return AgentDelegateAction(
                agent='StudyRepoForTaskAgent', inputs={'task': task}
            )

        last_observation = state.history[-1][1]
        if not isinstance(last_observation, AgentDelegateObservation):
            raise Exception('Last observation is not an AgentDelegateObservation')

        goal = state.get_current_user_intent()
        if self.current_delegate == 'study':
            self.current_delegate = 'coder'
            return AgentDelegateAction(
                agent='CoderAgent',
                inputs={
                    'task': goal,
                    'summary': last_observation.outputs['summary'],
                },
            )
        elif self.current_delegate == 'coder':
            self.current_delegate = 'verifier'
            return AgentDelegateAction(
                agent='VerifierAgent',
                inputs={
                    'task': goal,
                },
            )
        elif self.current_delegate == 'verifier':
            if (
                'completed' in last_observation.outputs
                and last_observation.outputs['completed']
            ):
                return AgentFinishAction()
            else:
                self.current_delegate = 'coder'
                return AgentDelegateAction(
                    agent='CoderAgent',
                    inputs={
                        'task': goal,
                        'summary': last_observation.outputs['summary'],
                    },
                )
        else:
            raise Exception('Invalid delegate state')

    def search_memory(self, query: str) -> list[str]:
        return []
