from enum import Enum

from openhands.sdk.llm import UNVERIFIED_MODELS_EXCLUDING_BEDROCK, VERIFIED_MODELS
from prompt_toolkit.completion import FuzzyWordCompleter
from pydantic import SecretStr

from openhands_cli.tui.utils import StepCounter
from openhands_cli.user_actions.utils import (
    NonEmptyValueValidator,
    cli_confirm,
    cli_text_input,
)


class SettingsType(Enum):
    BASIC = 'basic'
    ADVANCED = 'advanced'


def settings_type_confirmation(first_time: bool = False) -> SettingsType:
    question = (
            '\nWelcome to OpenHands! Let\'s configure your LLM settings.\n'
            'Choose your preferred setup method:'
        )
    choices = [
        'LLM (Basic)',
        'LLM (Advanced)'
    ]
    if not first_time:
        question = 'Which settings would you like to modify?'
        choices.append('Go back')


    index = cli_confirm(question, choices, escapable=True)

    if choices[index] == 'Go back':
        raise KeyboardInterrupt

    options_map = {0: SettingsType.BASIC, 1: SettingsType.ADVANCED}

    return options_map.get(index)


def choose_llm_provider(step_counter: StepCounter, escapable=True) -> str:
    question = step_counter.next_step(
        'Select LLM Provider (TAB for options, CTRL-c to cancel): '
    )
    options = (
        list(VERIFIED_MODELS.keys()).copy()
        + list(UNVERIFIED_MODELS_EXCLUDING_BEDROCK.keys()).copy()
    )
    alternate_option = 'Select another provider'

    display_options = options[:4] + [alternate_option]

    index = cli_confirm(question, display_options, escapable=escapable)
    chosen_option = display_options[index]
    if display_options[index] != alternate_option:
        return chosen_option

    question = step_counter.existing_step(
        'Type LLM Provider (TAB to complete, CTRL-c to cancel): '
    )
    return cli_text_input(
        question, escapable=True, completer=FuzzyWordCompleter(options, WORD=True)
    )


def choose_llm_model(step_counter: StepCounter, provider: str, escapable=True) -> str:
    """Choose LLM model using spec-driven approach. Return (model, deferred)."""

    models = VERIFIED_MODELS.get(
        provider, []
    ) + UNVERIFIED_MODELS_EXCLUDING_BEDROCK.get(provider, [])

    if provider == 'openhands':
        question = (
            step_counter.next_step('Select Available OpenHands Model:\n')
            + 'LLM usage is billed at the providers’ rates with no markup. Details: https://docs.all-hands.dev/usage/llms/openhands-llms'
        )
    else:
        question = step_counter.next_step(
            'Select LLM Model (TAB for options, CTRL-c to cancel): '
        )
    alternate_option = 'Select another model'
    display_options = models[:4] + [alternate_option]
    index = cli_confirm(question, display_options, escapable=escapable)
    chosen_option = display_options[index]

    if chosen_option != alternate_option:
        return chosen_option

    question = step_counter.existing_step(
        'Type model id (TAB to complete, CTRL-c to cancel): '
    )

    return cli_text_input(
        question, escapable=True, completer=FuzzyWordCompleter(models, WORD=True)
    )


def prompt_api_key(
    step_counter: StepCounter,
    provider: str,
    existing_api_key: SecretStr | None = None,
    escapable=True,
) -> str:
    helper_text = (
        '\nYou can find your OpenHands LLM API Key in the API Keys tab of OpenHands Cloud: '
        'https://app.all-hands.dev/settings/api-keys\n'
        if provider == 'openhands'
        else ''
    )

    if existing_api_key:
        masked_key = existing_api_key.get_secret_value()[:3] + '***'
        question = f'Enter API Key [{masked_key}] (CTRL-c to cancel, ENTER to keep current, type new to change): '
        # For existing keys, allow empty input to keep current key
        validator = None
    else:
        question = 'Enter API Key (CTRL-c to cancel): '
        # For new keys, require non-empty input
        validator = NonEmptyValueValidator()

    question = helper_text + step_counter.next_step(question)
    user_input = cli_text_input(
        question, escapable=escapable, validator=validator, is_password=True
    )
    
    # If user pressed ENTER with existing key (empty input), return the existing key
    if existing_api_key and not user_input.strip():
        return existing_api_key.get_secret_value()
    
    return user_input


# Advanced settings functions
def prompt_custom_model(step_counter: StepCounter, escapable=True) -> str:
    """Prompt for custom model name."""
    question = step_counter.next_step('Custom Model (CTRL-c to cancel): ')
    return cli_text_input(question, escapable=escapable)


def prompt_base_url(step_counter: StepCounter, escapable=True) -> str:
    """Prompt for base URL."""
    question = step_counter.next_step('Base URL (CTRL-c to cancel): ')
    return cli_text_input(
        question, escapable=escapable, validator=NonEmptyValueValidator()
    )


def choose_memory_condensation(step_counter: StepCounter, escapable=True) -> bool:
    """Choose memory condensation setting."""
    question = step_counter.next_step('Memory Condensation (CTRL-c to cancel): ')
    choices = ['Enable', 'Disable']

    index = cli_confirm(question, choices, escapable=escapable)
    return index == 0  # True for Enable, False for Disable


def save_settings_confirmation() -> bool:
    """Prompt user to confirm saving settings."""
    question = 'Save new settings? (They will take effect after restart)'
    discard = 'No, discard'
    options = ['Yes, save', discard]

    index = cli_confirm(question, options, escapable=True)
    if options[index] == discard:
        raise KeyboardInterrupt

    return options[index]
