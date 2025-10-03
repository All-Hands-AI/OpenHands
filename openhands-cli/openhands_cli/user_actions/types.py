from enum import Enum
from typing import Optional

from pydantic import BaseModel

from openhands.sdk.security.confirmation_policy import ConfirmationPolicyBase


class UserConfirmation(Enum):
    ACCEPT = 'accept'
    REJECT = 'reject'
    DEFER = 'defer'


class ConfirmationResult(BaseModel):
    decision: UserConfirmation
    policy_change: Optional[ConfirmationPolicyBase] = None
    reason: str = ''
