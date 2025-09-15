from enum import Enum

from prompt_toolkit.completion import FuzzyWordCompleter
from pydantic import SecretStr


from openhands.sdk.llm import (
    VERIFIED_MODELS,
    UNVERIFIED_MODELS_EXCLUDING_BEDROCK
)

from openhands_cli.user_actions.utils import cli_confirm, cli_text_input


class SettingsType(Enum):
    BASIC = 'basic'
    ADVANCED = 'advanced'


def settings_type_confirmation() -> SettingsType:
    question = 'Which settings would you like to modify?'
    choices = [
        'LLM (Basic)',
        'Go back',
    ]

    index = cli_confirm(question, choices)

    if choices[index] == 'Go back':
        raise KeyboardInterrupt

    options_map = {0: SettingsType.BASIC}

    return options_map.get(index)


def choose_llm_provider(escapable=True) -> str:
    question = 'Step (1/3) Select LLM Provider (TAB for options, CTRL-c to cancel): '
    options = list(VERIFIED_MODELS.keys()).copy() + list(UNVERIFIED_MODELS_EXCLUDING_BEDROCK.keys()).copy()
    alternate_option = 'Select another provider'

    display_options = options[:4] + [alternate_option]

    index = cli_confirm(question, display_options, escapable=escapable)
    chosen_option = display_options[index]
    if display_options[index] != alternate_option:
        return chosen_option

    question = '(Step 1/3) Type LLM Provider (TAB to complete, CTRL-c to cancel): '
    return cli_text_input(
        question, escapable=True, completer=FuzzyWordCompleter(options, WORD=True)
    )


def choose_llm_model(provider: str, escapable=True) -> str:
    """Choose LLM model using spec-driven approach. Return (model, deferred)."""

    models = VERIFIED_MODELS.get(provider, []) + UNVERIFIED_MODELS_EXCLUDING_BEDROCK.get(provider, [])
    question = '(Step 2/3) Select LLM Model (TAB for options, CTRL-c to cancel): '
    alternate_option = 'Select another model'
    display_options = models[:4] + [alternate_option]
    index = cli_confirm(question, display_options, escapable=escapable)
    chosen_option = display_options[index]

    if chosen_option != alternate_option:
        return chosen_option

    question = '(Step 2/3) Type model id (TAB to complete, CTRL-c to cancel): '

    return cli_text_input(
        question, escapable=True, completer=FuzzyWordCompleter(models, WORD=True)
    )


def prompt_api_key(
    existing_api_key: SecretStr | None = None, escapable=True
) -> tuple[str | None, bool]:
    if existing_api_key:
        masked_key = existing_api_key.get_secret_value()[:3] + '***'
        question = f'Enter API Key [{masked_key}] (CTRL-c to cancel, ENTER to keep current, type new to change): '
    else:
        question = 'Enter API Key (CTRL-c to cancel): '

    question = '(Step 3/3) ' + question
    return cli_text_input(question, escapable=escapable)


def save_settings_confirmation() -> bool:
    """Prompt user to confirm saving settings."""
    question = 'Save new settings? (They will take effect after restart)'
    discard = 'No, discard'
    options = ['Yes, save', discard]

    index = cli_confirm(question, options)
    if options[index] == discard:
        raise KeyboardInterrupt

    return options[index]
