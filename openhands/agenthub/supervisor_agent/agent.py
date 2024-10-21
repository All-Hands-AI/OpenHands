import copy
import logging
from typing import Dict, List

from openhands.agenthub.supervisor_agent.prompt import (
    adjust_milestones,
    get_initial_prompt,
)
from openhands.controller.agent import Agent
from openhands.controller.state.state import State
from openhands.core.config import AgentConfig
from openhands.core.message import Message, TextContent
from openhands.core.utils import json
from openhands.events.action import Action, AgentDelegateAction, AgentFinishAction
from openhands.events.action.agent import AgentRejectAction
from openhands.events.observation.delegate import AgentDelegateObservation
from openhands.llm.llm import LLM


class SupervisorAgent(Agent):
    VERSION = '1.0'
    """
    The Supervisor Agent is an agent that collects information from other agents
    and makes decisions based on the information.
    """

    current_delegate: str = ''
    sub_goals: List[Dict[str, str]] = []
    current_goal_index: int = 0
    summary: str = ''
    task: str = ''

    def __init__(self, llm: LLM, config: AgentConfig):
        """Initialize the Supervisor Agent with an LLM

        Parameters:
        - llm (LLM): The llm to be used by this agent
        """
        super().__init__(llm, config)
        # Set up logger
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.DEBUG)  # Set the logging level

    def step(self, state: State) -> Action:
        """Checks to see if current step is completed, returns AgentFinishAction if True.
        Otherwise, delegates the task to the next agent in the pipeline.

        Parameters:
        - state (State): The current state given the previous actions and observations

        Returns:
        - AgentFinishAction: If the last state was 'completed', 'verified', or 'abandoned'
        - AgentDelegateAction: The next agent to delegate the task to
        """
        self.logger.debug('Starting step with state: %s', state)
        # Example logic for breaking down tasks and delegating
        if not self.sub_goals:
            self.logger.debug('No sub-goals found, breaking down task.')
            task, _ = state.get_current_user_intent()
            self.sub_goals = self.break_down_task(task)
            self.logger.debug('Sub-goals: %s', self.sub_goals)
            # If the LLM returns an empty list, reject the action
            if self.sub_goals is None or self.sub_goals == []:
                return AgentRejectAction()

        if self.current_delegate == '':
            self.logger.debug("Current delegate is empty, assigning 'manager'.")
            # First subgoal as the current delegate is empty
            self.current_delegate = 'manager'
            return AgentDelegateAction(
                agent='ManagerAgent',
                inputs={'task': json.dumps(self.sub_goals[self.current_goal_index])},
            )
        elif self.current_delegate == 'manager':
            self.logger.debug("Current delegate is 'manager'.")
            last_observation = state.history.get_last_observation()

            if not isinstance(last_observation, AgentDelegateObservation):
                raise Exception('Last observation is not an AgentDelegateObservation')

            if last_observation.outputs.get('action', '') == 'reject':
                self.logger.debug('No summary found, creating adjustment prompt.')
                reason = getattr(last_observation, 'reason', '')
                # Ensure reason is a string
                prompt = self.create_adjustment_prompt(reason)
                # Get the sub-goals from the language model using the generated prompt
                self.sub_goals = self.get_sub_goals_from_llm(prompt)
                # Add the summary to the current sub-goal
                current_task = copy.deepcopy(self.sub_goals[self.current_goal_index])
                current_task['summary'] = (
                    f'Summary from previous milestones: {self.summary}'
                )
                return AgentDelegateAction(
                    agent='ManagerAgent', inputs={'task': json.dumps(current_task)}
                )
            else:
                # Append the current milestone and summary to the agent's summary
                summary = last_observation.outputs.get('summary', '')
                self.append_to_summary(
                    self.sub_goals[self.current_goal_index]['task'], summary
                )
                self.current_goal_index += 1

                if self.current_goal_index < len(self.sub_goals):
                    # Add the summary to the current sub-goal
                    current_task = copy.deepcopy(
                        self.sub_goals[self.current_goal_index]
                    )
                    current_task['summary'] = (
                        f'Summary from previous milestones: {self.summary}'
                    )

                    return AgentDelegateAction(
                        agent='ManagerAgent', inputs={'task': json.dumps(current_task)}
                    )

        return AgentFinishAction()

    def break_down_task(self, task: str) -> List[Dict[str, str]]:
        # Generate the initial prompt for breaking down the task
        prompt = get_initial_prompt(task)
        # Get the sub-goals from the language model using the generated prompt
        return self.get_sub_goals_from_llm(prompt)

    def should_interrupt(self, observation) -> bool:
        # Logic to determine if the task should be interrupted
        return False  # Placeholder

    def summarize_history(self, history) -> str:
        # Logic to summarize the history
        return 'summary'  # Placeholder

    def provide_guidance(self, state: State) -> Action:
        # Logic to provide high-level guidance
        return AgentFinishAction()  # Placeholder

    def create_adjustment_prompt(self, reason: str) -> str:
        return adjust_milestones(
            self.sub_goals,
            self.sub_goals[self.current_goal_index],
            reason,
            self.summary,
            self.task,
        )

    def get_sub_goals_from_llm(self, prompt: str) -> List[Dict[str, str]]:
        content = [TextContent(text=prompt)]
        message = Message(role='user', content=content)
        response = self.llm.completion(
            messages=self.llm.format_messages_for_llm(message)
        )
        return json.loads(response['choices'][0]['message']['content'])

    def append_to_summary(self, milestone_name: str, summary: str):
        """Appends the milestone name and summary to the agent's summary state."""
        self.summary += f'Milestone: {milestone_name}\nSummary: {summary}\n\n'
