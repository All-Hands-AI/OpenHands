from enum import Enum

from openhands_cli.user_actions.types import UserConfirmation
from openhands_cli.user_actions.utils import cli_confirm


class SettingsType(Enum):
    BASIC = 'basic'
    ADVANCED = 'advanced'


def settings_type_confirmation() -> tuple[UserConfirmation, SettingsType | None]:
    question = 'Which settings would you like to modify?'

    options =  [
        'LLM (Basic)',
        'LLM (Advanced)',
        'Go back',
    ]

    index = cli_confirm(question, options)  # Blocking UI, not escapable


    if index == 0:
        return UserConfirmation.ACCEPT, SettingsType.BASIC

    elif index == 1:
        return UserConfirmation.ACCEPT, SettingsType.ADVANCED

    return UserConfirmation.REJECT, None

