from enum import Enum

from openhands.sdk.security.confirmation_policy import ConfirmationPolicyBase
from pydantic import BaseModel


class UserConfirmation(Enum):
    ACCEPT = "accept"
    REJECT = "reject"
    DEFER = "defer"


class ConfirmationResult(BaseModel):
    decision: UserConfirmation
    policy_change: ConfirmationPolicyBase | None = None
    reason: str = ""
