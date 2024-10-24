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
        self.llm_config = llm.config

    def step(self, state: State) -> Action:
        self.logger.debug('Starting step with state: %s', state)
        self.logger.debug('LLM config: %s', self.llm_config)

        if not self.sub_goals:
            self.initialize_sub_goals(state)

        if self.current_delegate == '':
            self.current_delegate = 'CodeActAgent'
            return self.delegate_to_agent(
                'CodeActAgent', self.construct_task_details(self.prepare_current_task())
            )

        elif self.current_delegate == 'CodeActAgent':
            return self.handle_code_act_agent(state)

        return AgentFinishAction()

    def initialize_sub_goals(self, state: State):
        self.logger.debug('No sub-goals found, breaking down task.')
        self.task, _ = state.get_current_user_intent()
        self.sub_goals = self.break_down_task(self.task)
        self.logger.debug('Sub-goals: %s', self.sub_goals)
        if not self.sub_goals:
            return AgentRejectAction()

    def delegate_to_agent(self, agent_name: str, task: str) -> AgentDelegateAction:
        self.logger.debug(f'Delegating to agent: {agent_name}')

        return AgentDelegateAction(agent=agent_name, inputs={'task': task})

    def handle_code_act_agent(self, state: State) -> Action:
        self.logger.debug("Current delegate is 'CodeActAgent'.")
        last_observation = state.history.get_last_observation()

        if not isinstance(last_observation, AgentDelegateObservation):
            raise Exception('Last observation is not an AgentDelegateObservation')

        if last_observation.outputs.get('action', '') == 'reject':
            return self.handle_rejection(last_observation)

        return self.handle_success(last_observation)

    def handle_rejection(
        self, last_observation: AgentDelegateObservation
    ) -> AgentDelegateAction:
        self.logger.debug('No summary found, creating adjustment prompt.')
        reason = getattr(last_observation, 'reason', '')
        prompt = self.create_adjustment_prompt(reason)
        self.sub_goals = self.get_sub_goals_from_llm(prompt)
        current_task = self.prepare_current_task()
        return self.delegate_to_agent(
            'CodeActAgent', self.construct_task_details(current_task)
        )

    def handle_success(self, last_observation: AgentDelegateObservation) -> Action:
        summary = last_observation.outputs.get('summary', '')
        self.append_to_summary(summary)
        self.current_goal_index += 1

        if self.current_goal_index < len(self.sub_goals):
            current_task = self.prepare_current_task()
            task_details = self.construct_task_details(current_task)
            return self.delegate_to_agent('CodeActAgent', task_details)

        return AgentFinishAction()

    def prepare_current_task(self) -> Dict[str, str]:
        current_task = copy.deepcopy(self.sub_goals[self.current_goal_index])
        current_task['summary'] = self.summary if self.summary else ''
        return current_task

    def construct_task_details(self, current_task: Dict[str, str]) -> str:
        task_details = (
            f"Task: {self.task}\n\n"
            f"Next Subtask: {current_task['task']}\n"
            f"Suggested Approach: {current_task['suggested_approach']}\n"
            f"Important Details: {current_task['important_details']}"
        )
        if self.summary:
            task_details = f'Progress so far: {self.summary}\n\n' + task_details
        return task_details

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

    def append_to_summary(self, summary: str):
        """Appends the milestone name and summary to the agent's summary state."""
        self.summary += f'{summary}\n\n'
