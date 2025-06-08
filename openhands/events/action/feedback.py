from dataclasses import dataclass
from typing import Optional

from openhands.core.schema import ActionType
from openhands.events.action.action import Action


@dataclass
class UserFeedbackAction(Action):
    """An action where the user provides feedback on the agent's performance.

    Attributes:
        rating (int): The user's rating of the agent's performance (1-5).
        reason (Optional[str]): The reason for the rating, if provided.
        action (str): The action type, namely ActionType.USER_FEEDBACK.
    """

    rating: int
    reason: Optional[str] = None
    action: str = "user_feedback"  # This will be added to ActionType

    @property
    def message(self) -> str:
        msg = f"User rated the agent's performance: {self.rating}/5"
        if self.reason:
            msg += f" - Reason: {self.reason}"
        return msg