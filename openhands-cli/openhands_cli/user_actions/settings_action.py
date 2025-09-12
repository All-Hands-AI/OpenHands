from enum import Enum

from openhands_cli.user_actions.types import UserConfirmation
from openhands_cli.user_actions.utils import cli_confirm, prompt_user

from openhands_cli.tui.settings.constants import VERIFIED_PROVIDERS
from pydantic import SecretStr


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



def choose_llm_provider() -> str:
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



def choose_llm_model() -> str:
    question = '(Step 2/3) Select LLM Model (TAB for options, CTRL-c to cancel)'



def specify_api_key(existing_api_key: SecretStr | None) -> str | None:
    if existing_api_key:
        question = f'(Step 3/3) Enter API Key [{existing_api_key.get_secret_value()[0:3]}***] (CTRL-c to cancel, ENTER to keep current, type new to change):'
    else:

        question = '(Step 3/3) Enter API Key (CTRL-c to cancel):'

    response, defer = prompt_user(question)
    if defer:
        return None

    return response


def save_settings_confirmation():
    question = 'Save new settings? (They will take effect after restart)'
    options = [
        'Yes, save',
        'No, discard'
    ]

    index = cli_confirm(question, options)
    options_mapping = {
        0: UserConfirmation.ACCEPT,
        1: UserConfirmation.REJECT,
    }
    return options_mapping.get(index, UserConfirmation.REJECT)

