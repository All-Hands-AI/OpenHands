import enum
from typing import Any


class TaskState:
    def __init__(
        self,
        finished: bool = False,
        success: bool = False,
        agent_action_count: dict = None,
        terminate_reason: str = None,
        latest_output: dict[str, Any] = None,
    ):
        self.finished = finished
        self.success = success
        self.agent_action_count: dict[str, int] = (
            agent_action_count
            if agent_action_count
            else {
                'propose_solution': 0,
                'use_tool': 0,
                'invalid_action': 0,
            }
        )
        self.terminate_reason = terminate_reason
        self.latest_output = latest_output

    def to_dict(self) -> dict[str, Any]:
        return {
            'finished': self.finished,
            'success': self.success,
            'agent_action_count': self.agent_action_count,
            'terminate_reason': self.terminate_reason,
            'latest_output': self.latest_output,
        }


class ParseError(Exception):
    pass


class FeedbackType(enum.Enum):
    FEEDBACK_WITH_GT = 'feedback_with_gt'
    FEEDBACK_WO_GT = 'feedback_wo_gt'
    NO_FEEDBACK = 'no_feedback'


class StepOutput:
    def __init__(
        self,
        observation: str = None,
        success: bool = False,
        extra: dict[str, Any] = None,
        turn_info: tuple[int, int] = None,
    ):
        self.observation: str = observation
        self.success: bool = success
        self.extra: dict[str, Any] = extra
        self.turn_info = turn_info

    def __repr__(self) -> str:
        return self.observation

    def to_str(self) -> str:
        output = 'Observation:\n'
        if self.observation is not None:
            output += self.observation + '\n'
        else:
            if not self.success:
                output += 'Your answer is wrong.\n'

        if self.turn_info is not None:
            n_steps_left, n_propose_solution_left = self.turn_info
            output += 'You have {} steps left and {} chances to propose solution left.\n'.format(
                n_steps_left, n_propose_solution_left
            )
            if n_steps_left <= 1:
                output += 'You should take the last step to propose a solution.\n'

        return output

    def to_dict(self) -> dict[str, Any]:
        return {
            'observation': self.observation,
            'success': self.success,
        }
