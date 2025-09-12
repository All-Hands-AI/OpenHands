from enum import Enum

from openhands_cli.user_actions.types import UserConfirmation
from openhands_cli.user_actions.utils import cli_confirm, prompt_user

from openhands_cli.tui.settings.constants import VERIFIED_PROVIDERS


class SettingsType(Enum):
    BASIC = 'basic'
    ADVANCED = 'advanced'


def settings_type_confirmation() -> tuple[UserConfirmation, SettingsType | None]:
    question = 'Which settings would you like to modify?'

    options =  [
        'LLM (Basic)',
        'Go back',
    ]

    index = cli_confirm(question, options)  # Blocking UI, not escapable


    if index == 0:
        return UserConfirmation.ACCEPT, SettingsType.BASIC

    return UserConfirmation.REJECT, None



def choose_settings_provider() -> str:
    question = '(Step 1/3) Select LLM Provider:'

    options = VERIFIED_PROVIDERS.copy()
    options.append('Select another provider')

    index = cli_confirm(question, options)
    if options[index] == 'Select another provider':
        # TODO: implement autocomplete for other provider selections
        followup_question = '(Step 1/3) Select LLM Provider (TAB for options, CTRL-c to cancel):'
        response, _ = prompt_user(followup_question, escapable=False)
        return response


    return options[index]


