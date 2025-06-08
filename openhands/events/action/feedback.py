from dataclasses import dataclass
from typing import Literal, Optional

from openhands.core.schema import ActionType
from openhands.events.action.action import Action


@dataclass
class UserFeedbackAction(Action):
    """An action where the user provides feedback on a message or the entire trajectory.

    Attributes:
        feedback_type (str): The type of feedback, either "positive" or "negative".
        target_type (str): The target of the feedback, either "message" or "trajectory".
        target_id (Optional[int]): The ID of the target message, if target_type is "message".
        rating (Optional[int]): A numeric rating from 1-5 for the feedback (used in SAAS mode).
        reason (Optional[str]): A reason for the feedback (used in SAAS mode).
        action (str): The action type, namely ActionType.USER_FEEDBACK.
    """

    feedback_type: Literal["positive", "negative"]
    target_type: Literal["message", "trajectory"]
    target_id: Optional[int] = None
    rating: Optional[int] = None
    reason: Optional[str] = None
    action: str = ActionType.USER_FEEDBACK

    @property
    def message(self) -> str:
        if self.target_type == "message":
            return f"User provided {self.feedback_type} feedback for message {self.target_id}"
        return f"User provided {self.feedback_type} feedback for the trajectory"