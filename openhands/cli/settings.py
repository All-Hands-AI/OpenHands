from prompt_toolkit import PromptSession, print_formatted_text
from prompt_toolkit.completion import FuzzyWordCompleter
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.shortcuts import print_container
from prompt_toolkit.widgets import Frame, TextArea
from pydantic import SecretStr

from openhands.cli.tui import (
    COLOR_GREY,
    UserCancelledError,
    cli_confirm,
    kb_cancel,
)
from openhands.cli.utils import (
    VERIFIED_ANTHROPIC_MODELS,
    VERIFIED_OPENAI_MODELS,
    VERIFIED_PROVIDERS,
    organize_models_and_providers,
)
from openhands.controller.agent import Agent
from openhands.core.config import AppConfig
from openhands.core.config.condenser_config import NoOpCondenserConfig
from openhands.core.config.utils import OH_DEFAULT_AGENT
from openhands.memory.condenser.impl.llm_summarizing_condenser import (
    LLMSummarizingCondenserConfig,
)
from openhands.storage.data_models.settings import Settings
from openhands.storage.settings.file_settings_store import FileSettingsStore
from openhands.utils.llm import get_supported_llm_models


def display_settings(config: AppConfig):
    llm_config = config.get_llm_config()
    advanced_llm_settings = True if llm_config.base_url else False

    # Prepare labels and values based on settings
    labels_and_values = []
    if not advanced_llm_settings:
        # Attempt to determine provider, fallback if not directly available
        provider = getattr(
            llm_config,
            'provider',
            llm_config.model.split('/')[0] if '/' in llm_config.model else 'Unknown',
        )
        labels_and_values.extend(
            [
                ('   LLM Provider', str(provider)),
                ('   LLM Model', str(llm_config.model)),
                ('   API Key', '********' if llm_config.api_key else 'Not Set'),
            ]
        )
    else:
        labels_and_values.extend(
            [
                ('   Custom Model', str(llm_config.model)),
                ('   Base URL', str(llm_config.base_url)),
                ('   API Key', '********' if llm_config.api_key else 'Not Set'),
            ]
        )

    # Common settings
    labels_and_values.extend(
        [
            ('   Agent', str(config.default_agent)),
            (
                '   Confirmation Mode',
                'Enabled' if config.security.confirmation_mode else 'Disabled',
            ),
            (
                '   Memory Condensation',
                'Enabled' if config.enable_default_condenser else 'Disabled',
            ),
        ]
    )

    # Calculate max widths for alignment
    # Ensure values are strings for len() calculation
    str_labels_and_values = [(label, str(value)) for label, value in labels_and_values]
    max_label_width = (
        max(len(label) for label, _ in str_labels_and_values)
        if str_labels_and_values
        else 0
    )

    # Construct the summary text with aligned columns
    settings_lines = [
        f'{label+":":<{max_label_width+1}} {value:<}'  # Changed value alignment to left (<)
        for label, value in str_labels_and_values
    ]
    settings_text = '\n'.join(settings_lines)

    container = Frame(
        TextArea(
            text=settings_text,
            read_only=True,
            style=COLOR_GREY,
            wrap_lines=True,
        ),
        title='Settings',
        style=f'fg:{COLOR_GREY}',
    )

    print_container(container)


async def get_validated_input(
    session: PromptSession,
    prompt_text: str,
    completer=None,
    validator=None,
    error_message='Input cannot be empty',
):
    session.completer = completer
    value = None

    while True:
        value = await session.prompt_async(prompt_text)

        if validator:
            is_valid = validator(value)
            if not is_valid:
                print_formatted_text('')
                print_formatted_text(HTML(f'<grey>{error_message}: {value}</grey>'))
                print_formatted_text('')
                continue
        elif not value:
            print_formatted_text('')
            print_formatted_text(HTML(f'<grey>{error_message}</grey>'))
            print_formatted_text('')
            continue

        break

    return value


def save_settings_confirmation() -> bool:
    return (
        cli_confirm(
            '\nSave new settings? (They will take effect after restart)',
            ['Yes, save', 'No, discard'],
        )
        == 0
    )


async def modify_llm_settings_basic(
    config: AppConfig, settings_store: FileSettingsStore
):
    model_list = get_supported_llm_models(config)
    organized_models = organize_models_and_providers(model_list)

    provider_list = list(organized_models.keys())
    verified_providers = [p for p in VERIFIED_PROVIDERS if p in provider_list]
    provider_list = [p for p in provider_list if p not in verified_providers]
    provider_list = verified_providers + provider_list

    provider_completer = FuzzyWordCompleter(provider_list)
    session = PromptSession(key_bindings=kb_cancel())

    provider = None
    model = None
    api_key = None

    try:
        provider = await get_validated_input(
            session,
            '(Step 1/3) Select LLM Provider (TAB for options, CTRL-c to cancel): ',
            completer=provider_completer,
            validator=lambda x: x in organized_models,
            error_message='Invalid provider selected',
        )

        model_list = organized_models[provider]['models']
        if provider == 'openai':
            model_list = [m for m in model_list if m not in VERIFIED_OPENAI_MODELS]
            model_list = VERIFIED_OPENAI_MODELS + model_list
        if provider == 'anthropic':
            model_list = [m for m in model_list if m not in VERIFIED_ANTHROPIC_MODELS]
            model_list = VERIFIED_ANTHROPIC_MODELS + model_list

        model_completer = FuzzyWordCompleter(model_list)
        model = await get_validated_input(
            session,
            '(Step 2/3) Select LLM Model (TAB for options, CTRL-c to cancel): ',
            completer=model_completer,
            validator=lambda x: x in organized_models[provider]['models'],
            error_message=f'Invalid model selected for provider {provider}',
        )

        api_key = await get_validated_input(
            session,
            '(Step 3/3) Enter API Key (CTRL-c to cancel): ',
            error_message='API Key cannot be empty',
        )

    except (
        UserCancelledError,
        KeyboardInterrupt,
        EOFError,
    ):
        return  # Return on exception

    # TODO: check for empty string inputs?
    # Handle case where a prompt might return None unexpectedly
    if provider is None or model is None or api_key is None:
        return

    save_settings = save_settings_confirmation()

    if not save_settings:
        return

    llm_config = config.get_llm_config()
    llm_config.model = provider + organized_models[provider]['separator'] + model
    llm_config.api_key = SecretStr(api_key)
    llm_config.base_url = None
    config.set_llm_config(llm_config)

    config.default_agent = OH_DEFAULT_AGENT
    config.security.confirmation_mode = False
    config.enable_default_condenser = True

    agent_config = config.get_agent_config(config.default_agent)
    agent_config.condenser = LLMSummarizingCondenserConfig(
        llm_config=llm_config,
        type='llm',
    )
    config.set_agent_config(agent_config, config.default_agent)

    settings = await settings_store.load()
    if not settings:
        settings = Settings()

    settings.llm_model = provider + organized_models[provider]['separator'] + model
    settings.llm_api_key = SecretStr(api_key)
    settings.llm_base_url = None
    settings.agent = OH_DEFAULT_AGENT
    settings.confirmation_mode = False
    settings.enable_default_condenser = True

    await settings_store.store(settings)


async def modify_llm_settings_advanced(
    config: AppConfig, settings_store: FileSettingsStore
):
    session = PromptSession(key_bindings=kb_cancel())

    custom_model = None
    base_url = None
    api_key = None
    agent = None

    try:
        custom_model = await get_validated_input(
            session,
            '(Step 1/6) Custom Model (CTRL-c to cancel): ',
            error_message='Custom Model cannot be empty',
        )

        base_url = await get_validated_input(
            session,
            '(Step 2/6) Base URL (CTRL-c to cancel): ',
            error_message='Base URL cannot be empty',
        )

        api_key = await get_validated_input(
            session,
            '(Step 3/6) API Key (CTRL-c to cancel): ',
            error_message='API Key cannot be empty',
        )

        agent_list = Agent.list_agents()
        agent_completer = FuzzyWordCompleter(agent_list)
        agent = await get_validated_input(
            session,
            '(Step 4/6) Agent (TAB for options, CTRL-c to cancel): ',
            completer=agent_completer,
            validator=lambda x: x in agent_list,
            error_message='Invalid agent selected',
        )

        enable_confirmation_mode = (
            cli_confirm(
                question='(Step 5/6) Confirmation Mode (CTRL-c to cancel):',
                choices=['Enable', 'Disable'],
            )
            == 0
        )

        enable_memory_condensation = (
            cli_confirm(
                question='(Step 6/6) Memory Condensation (CTRL-c to cancel):',
                choices=['Enable', 'Disable'],
            )
            == 0
        )

    except (
        UserCancelledError,
        KeyboardInterrupt,
        EOFError,
    ):
        return  # Return on exception

    # TODO: check for empty string inputs?
    # Handle case where a prompt might return None unexpectedly
    if custom_model is None or base_url is None or api_key is None or agent is None:
        return

    save_settings = save_settings_confirmation()

    if not save_settings:
        return

    llm_config = config.get_llm_config()
    llm_config.model = custom_model
    llm_config.base_url = base_url
    llm_config.api_key = SecretStr(api_key)
    config.set_llm_config(llm_config)

    config.default_agent = agent

    config.security.confirmation_mode = enable_confirmation_mode

    agent_config = config.get_agent_config(config.default_agent)
    if enable_memory_condensation:
        agent_config.condenser = LLMSummarizingCondenserConfig(
            llm_config=llm_config,
            type='llm',
        )
    else:
        agent_config.condenser = NoOpCondenserConfig(type='noop')
    config.set_agent_config(agent_config)

    settings = await settings_store.load()
    if not settings:
        settings = Settings()

    settings.llm_model = custom_model
    settings.llm_api_key = SecretStr(api_key)
    settings.llm_base_url = base_url
    settings.agent = agent
    settings.confirmation_mode = enable_confirmation_mode
    settings.enable_default_condenser = enable_memory_condensation

    await settings_store.store(settings)
