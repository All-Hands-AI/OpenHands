from enum import Enum
from prompt_toolkit.validation import Validator, ValidationError


class UserConfirmation(Enum):
    ACCEPT = "accept"
    REJECT = "reject"
    DEFER = "defer"
    ALWAYS_ACCEPT = "always_accept"


class NonEmptyValueValidator(Validator):
    def validate(self, document):
        text = document.text
        if not text:
            raise ValidationError(
                message="API key cannot be empty. Please enter a valid API key."
            )
