from enum import Enum


class UserConfirmation(Enum):
    ACCEPT = "accept"
    REJECT = "reject"
    DEFER = "defer"
    ALWAYS_ACCEPT = "always_accept"
