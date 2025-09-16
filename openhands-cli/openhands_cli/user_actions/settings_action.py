from enum import Enum

from prompt_toolkit.completion import FuzzyWordCompleter
from pydantic import SecretStr


from openhands.sdk.llm import (
    VERIFIED_MODELS,
    UNVERIFIED_MODELS_EXCLUDING_BEDROCK
)

from openhands_cli.user_actions.utils import cli_confirm, cli_text_input
from prompt_toolkit.validation import Validator, ValidationError


class NonEmptyValueValidator(Validator):
    def validate(self, document):
        text = document.text
        if not text:
            raise ValidationError(
                message="API key cannot be empty. Please enter a valid API key."
            )


class StepCounter:
    """Automatically manages step numbering for settings flows."""

    def __init__(self, total_steps: int):
        self.current_step = 0
        self.total_steps = total_steps

    def next_step(self, prompt: str) -> str:
        """Get the next step prompt with automatic numbering."""
        self.current_step += 1
        return f"(Step {self.current_step}/{self.total_steps}) {prompt}"


def format_step_prompt(step: int, total_steps: int, prompt: str) -> str:
    """Legacy function for backward compatibility with basic settings."""
    return f"(Step {step}/{total_steps}) {prompt}"


class SettingsType(Enum):
    BASIC = 'basic'
    ADVANCED = 'advanced'


def settings_type_confirmation() -> SettingsType:
    question = 'Which settings would you like to modify?'
    choices = [
        'LLM (Basic)',
        'LLM (Advanced)',
        'Search API (Optional)',
        'Go back',
    ]

    index = cli_confirm(question, choices)

    if choices[index] == 'Go back':
        raise KeyboardInterrupt

    options_map = {
        0: SettingsType.BASIC,
        1: SettingsType.ADVANCED,
        2: None,  # Search API - not implemented yet
    }

    return options_map.get(index)


def choose_llm_provider(escapable=True) -> str:
    question = format_step_prompt(1, 3, 'Select LLM Provider (TAB for options, CTRL-c to cancel): ')
    options = list(VERIFIED_MODELS.keys()).copy() + list(UNVERIFIED_MODELS_EXCLUDING_BEDROCK.keys()).copy()
    alternate_option = 'Select another provider'

    display_options = options[:4] + [alternate_option]

    index = cli_confirm(question, display_options, escapable=escapable)
    chosen_option = display_options[index]
    if display_options[index] != alternate_option:
        return chosen_option

    question = format_step_prompt(1, 3, 'Type LLM Provider (TAB to complete, CTRL-c to cancel): ')
    return cli_text_input(
        question, escapable=True, completer=FuzzyWordCompleter(options, WORD=True)
    )


def choose_llm_model(provider: str, escapable=True) -> str:
    """Choose LLM model using spec-driven approach. Return (model, deferred)."""

    models = VERIFIED_MODELS.get(provider, []) + UNVERIFIED_MODELS_EXCLUDING_BEDROCK.get(provider, [])

    if provider == 'openhands':
        question = (
            format_step_prompt(2, 3, 'Select Available OpenHands Model:\n')
            + 'LLM usage is billed at the providers’ rates with no markup. Details: https://docs.all-hands.dev/usage/llms/openhands-llms'
        )
    else:
        question = format_step_prompt(2, 3, 'Select LLM Model (TAB for options, CTRL-c to cancel): ')
    alternate_option = 'Select another model'
    display_options = models[:4] + [alternate_option]
    index = cli_confirm(question, display_options, escapable=escapable)
    chosen_option = display_options[index]

    if chosen_option != alternate_option:
        return chosen_option

    question = format_step_prompt(2, 3, 'Type model id (TAB to complete, CTRL-c to cancel): ')

    return cli_text_input(
        question, escapable=True, completer=FuzzyWordCompleter(models, WORD=True)
    )



def prompt_api_key(
    provider: str, existing_api_key: SecretStr | None = None, escapable=True
) -> tuple[str | None, bool]:
    helper_text = (
        "\nYou can find your OpenHands LLM API Key in the API Keys tab of OpenHands Cloud: "
        "https://app.all-hands.dev/settings/api-keys\n"
        if provider == "openhands"
        else ""
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

    question = helper_text + format_step_prompt(3, 3, question)
    return cli_text_input(question, escapable=escapable, validator=validator, is_password=True)


# Advanced settings functions
def prompt_custom_model(question: str, escapable=True) -> str:
    """Prompt for custom model name."""
    return cli_text_input(question, escapable=escapable)


def prompt_base_url(question: str, escapable=True) -> str:
    """Prompt for base URL."""
    return cli_text_input(question, escapable=escapable, validator=NonEmptyValueValidator())


def prompt_advanced_api_key(question: str, existing_api_key: SecretStr | None = None, escapable=True) -> str:
    """Prompt for API key in advanced settings."""
    if existing_api_key:
        # For existing keys, allow empty input to keep current key
        validator = None
    else:
        # For new keys, require non-empty input
        validator = NonEmptyValueValidator()

    return cli_text_input(question, escapable=escapable, validator=validator, is_password=True)


def choose_agent(question: str, escapable=True) -> str:
    """Choose agent type."""
    # Available agents based on the agenthub
    agents = [
        'CodeActAgent',
        'BrowsingAgent',
        'VisualBrowsingAgent',
        'ReadOnlyAgent',
        'LocAgent',
    ]

    index = cli_confirm(question, agents, escapable=escapable)
    return agents[index]


def choose_confirmation_mode(question: str, escapable=True) -> bool:
    """Choose confirmation mode setting."""
    choices = ['Enable', 'Disable']

    index = cli_confirm(question, choices, escapable=escapable)
    return index == 0  # True for Enable, False for Disable


def choose_memory_condensation(question: str, escapable=True) -> bool:
    """Choose memory condensation setting."""
    choices = ['Enable', 'Disable']

    index = cli_confirm(question, choices, escapable=escapable)
    return index == 0  # True for Enable, False for Disable


def save_settings_confirmation() -> bool:
    """Prompt user to confirm saving settings."""
    question = 'Save new settings? (They will take effect after restart)'
    discard = 'No, discard'
    options = ['Yes, save', discard]

    index = cli_confirm(question, options)
    if options[index] == discard:
        raise KeyboardInterrupt

    return options[index]
