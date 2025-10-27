from openhands_cli.user_actions.types import UserConfirmation
from openhands_cli.user_actions.utils import cli_confirm


def exit_session_confirmation() -> UserConfirmation:
    """
    Ask user to confirm exiting session.
    """

    question = 'Terminate session?'
    options = ['Yes, proceed', 'No, dismiss']
    index = cli_confirm(question, options)  # Blocking UI, not escapable

    options_mapping = {
        0: UserConfirmation.ACCEPT,  # User accepts termination session
        1: UserConfirmation.REJECT,  # User does not terminate session
    }
    return options_mapping.get(index, UserConfirmation.REJECT)
