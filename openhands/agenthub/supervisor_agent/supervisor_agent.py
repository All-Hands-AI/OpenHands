from collections import deque

from openhands.controller.agent import Agent
from openhands.controller.state.state import State
from openhands.core.config import AgentConfig
from openhands.core.logger import openhands_logger as logger
from openhands.events.action import (
    Action,
    AgentDelegateAction,
    AgentFinishAction,
    AgentFinishTaskCompleted,
)
from openhands.llm.llm import LLM


class SupervisorAgent(Agent):
    VERSION = '1.0'
    """
    The Supervisor Agent delegates tasks to other agents and monitors their execution.

    Currently, it simply delegates to CodeActAgent and finishes when CodeActAgent is done.

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

    def step(self, state: State) -> Action:
        """Performs one step using the Supervisor Agent.

        This method delegates to CodeActAgent on the first step,
        and returns AgentFinishAction when the delegated agent is done.

        Parameters:
        - state (State): used to get updated info

        Returns:
        - AgentDelegateAction - delegate to CodeActAgent
        - AgentFinishAction - finish when CodeActAgent is done
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
                        'SupervisorAgent: CodeActAgent has finished, completing task'
                    )
                    self.finished = True
                    return AgentFinishAction(
                        final_thought="The CodeActAgent has completed the task. I've supervised the execution and everything is complete.",
                        task_completed=AgentFinishTaskCompleted.TRUE,
                    )

        # If we're here, we're waiting for the delegated agent to finish
        logger.info('SupervisorAgent: Waiting for CodeActAgent to complete')
        return AgentFinishAction(
            final_thought="The CodeActAgent has completed the task. I've supervised the execution and everything is complete.",
            task_completed=AgentFinishTaskCompleted.TRUE,
        )
