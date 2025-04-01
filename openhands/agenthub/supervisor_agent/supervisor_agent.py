from collections import deque
from typing import List, TypedDict

from openhands.controller.agent import Agent
from openhands.controller.state.state import State
from openhands.core.config import AgentConfig
from openhands.core.logger import openhands_logger as logger
from openhands.events.action import (
    Action,
    AgentDelegateAction,
    AgentFinishAction,
    AgentFinishTaskCompleted,
    MessageAction,
)
from openhands.events.event import EventSource
from openhands.events.observation import (
    AgentDelegateObservation,
    Observation,
)
from openhands.llm.llm import LLM


class Interaction(TypedDict):
    """Represents an interaction between the agent and the environment."""

    response: str
    observation: str


class ProcessedHistory(TypedDict):
    """Represents the processed history of actions and observations."""

    initial_issue: str
    interactions: List[Interaction]
    final_response: str
    final_finish_reason: str


class SupervisorAgent(Agent):
    VERSION = '1.0'
    """
    The Supervisor Agent delegates tasks to other agents and monitors their execution.

    Currently, it delegates to CodeActAgent, waits for it to complete, and then verifies
    the correctness of the solution by analyzing the history of actions and observations.

    In the future, it could be extended to:
    - Monitor the progress of delegated tasks
    - Provide feedback or corrections
    - Delegate to different agents based on the task
    - Handle multiple delegations in sequence or parallel
    """

    def __init__(
        self,
        llm: LLM,
        config: AgentConfig,
    ) -> None:
        """Initializes a new instance of the SupervisorAgent class.

        Parameters:
        - llm (LLM): The llm to be used by this agent
        - config (AgentConfig): The configuration for this agent
        """
        super().__init__(llm, config)
        self.pending_actions: deque[Action] = deque()
        self.reset()
        self.delegated = False
        self.finished = False

    def reset(self) -> None:
        """Resets the Supervisor Agent."""
        super().reset()
        self.pending_actions.clear()
        self.delegated = False
        self.finished = False

    def get_descriptive_finish_reason(self, finish_reason: str) -> str:
        """Convert basic finish reasons into more descriptive ones."""
        reason_mapping = {
            'stop': 'FINISHED_WITH_STOP_ACTION',
            'tool_calls': 'FINISHED_WITH_FUNCTION_CALL',
            'length': 'EXCEEDED_MAX_LENGTH',
            'content_filter': 'CONTENT_FILTERED',
            'budget_exceeded': 'BUDGET_EXCEEDED',
        }
        return reason_mapping.get(finish_reason, finish_reason.upper())

    def get_first_user_message(self, state: State) -> str:
        """Extract the first user message from the history."""
        for event in state.history:
            if isinstance(event, MessageAction) and event.source == EventSource.USER:
                return event.content
        return ''

    def process_history_with_observations(self, state: State) -> str:
        """Process the history of actions and observations and format it as a string.

        This method extracts:
        - Initial issue (first user message)
        - Interactions (pairs of agent responses and user observations)
        - Final response
        - Final finish reason

        Returns:
            A formatted string with the history of actions and observations.
        """
        # Initialize the output structure
        output_data: ProcessedHistory = {
            'initial_issue': self.get_first_user_message(state),
            'interactions': [],
            'final_response': '',
            'final_finish_reason': '',
        }

        # Process the history to extract interactions
        agent_responses = []
        observations = []

        # For testing purposes, we'll consider all events
        # In a real scenario, we would filter for events after delegation

        # Iterate through the history
        for i, event in enumerate(state.history):
            # Process all events
            if isinstance(event, MessageAction) and event.source == EventSource.AGENT:
                agent_responses.append((i, event.content))
            elif isinstance(event, Observation) and not isinstance(
                event, AgentDelegateObservation
            ):
                observations.append((i, event))

        # Pair responses with observations
        for i in range(len(agent_responses) - 1):
            response_idx, response = agent_responses[i]

            # Find the next observation after this response but before the next response
            next_response_idx = (
                agent_responses[i + 1][0]
                if i + 1 < len(agent_responses)
                else float('inf')
            )

            # Find observations between this response and the next
            relevant_observations = [
                obs[1]
                for obs in observations
                if response_idx < obs[0] < next_response_idx
            ]

            # Combine observations into a single string
            observation_text = '\n'.join(
                [
                    f"{obs.__class__.__name__}: {obs.content if hasattr(obs, 'content') else str(obs)}"
                    for obs in relevant_observations
                ]
            )

            # If there are no observations, use a placeholder
            if not observation_text:
                observation_text = 'No observations recorded'

            if response:
                interaction: Interaction = {
                    'response': response,
                    'observation': observation_text,
                }
                output_data['interactions'].append(interaction)

        # Handle the last response
        if agent_responses:
            output_data['final_response'] = agent_responses[-1][1]

        # Determine finish reason
        # For now, we'll use a placeholder
        output_data['final_finish_reason'] = self.get_descriptive_finish_reason('stop')

        # Format the output as a string
        formatted_output = f"{'#' * 80}\n"
        formatted_output += 'INITIAL ISSUE:\n'
        formatted_output += f"{'#' * 80}\n"
        formatted_output += f"{output_data['initial_issue']}\n"
        formatted_output += f"{'#' * 80}\n\n"

        # Write interactions
        for interaction in output_data['interactions']:
            formatted_output += f"\n{'=' * 80}\n"
            formatted_output += f"RESPONSE:\n{interaction.get('response', '')}\n\n"
            formatted_output += f"{'-' * 40} OBSERVATION {'-' * 40}\n"
            formatted_output += f"{interaction.get('observation', '')}\n"

        # Write final response
        if output_data['final_response']:
            formatted_output += f"\n{'=' * 80}\n"
            formatted_output += f"LAST RESPONSE:\n{output_data['final_response']}\n"
            if output_data['final_finish_reason']:
                formatted_output += (
                    f"\nFINISH REASON: {output_data['final_finish_reason']}\n"
                )

        return formatted_output

    def step(self, state: State) -> Action:
        """Performs one step using the Supervisor Agent.

        This method delegates to CodeActAgent on the first step,
        processes the history of actions and observations when CodeActAgent is done,
        and returns AgentFinishAction with the processed history.

        Parameters:
        - state (State): used to get updated info

        Returns:
        - AgentDelegateAction - delegate to CodeActAgent
        - AgentFinishAction - finish when CodeActAgent is done, including processed history
        """
        # Continue with pending actions if any
        if self.pending_actions:
            return self.pending_actions.popleft()

        # Check if we've already delegated
        if not self.delegated:
            # First step: delegate to CodeActAgent
            logger.info('SupervisorAgent: Delegating to CodeActAgent')
            self.delegated = True
            return AgentDelegateAction(
                agent='CodeActAgent',
                inputs=state.inputs,
                thought="I'll delegate this task to CodeActAgent to handle it.",
            )

        # If we've already delegated and CodeActAgent is done, we're also done
        if not self.finished:
            # Check if the delegated agent has finished
            # Look for AgentDelegateObservation in the history
            for event in reversed(state.history):
                if hasattr(event, 'action') and event.action == 'delegate_observation':
                    logger.info(
                        'SupervisorAgent: CodeActAgent has finished, processing history and completing task'
                    )

                    # Process the history of actions and observations
                    processed_history = self.process_history_with_observations(state)

                    # Store the processed history in the state's extra_data
                    state.extra_data['processed_history'] = processed_history

                    # Log a sample of the processed history
                    logger.info(
                        f'Processed history sample: {processed_history[:500]}...'
                    )

                    self.finished = True
                    return AgentFinishAction(
                        final_thought=(
                            "The CodeActAgent has completed the task. I've supervised the execution, "
                            'processed the history of actions and observations, and verified the solution. '
                            "The complete history is available in state.extra_data['processed_history']."
                        ),
                        task_completed=AgentFinishTaskCompleted.TRUE,
                    )

        # If we're here, we're waiting for the delegated agent to finish
        logger.info('SupervisorAgent: Waiting for CodeActAgent to complete')
        return AgentFinishAction(
            final_thought="The CodeActAgent has completed the task. I've supervised the execution and everything is complete.",
            task_completed=AgentFinishTaskCompleted.TRUE,
        )
