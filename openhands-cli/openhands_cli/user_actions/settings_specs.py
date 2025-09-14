"""Declarative prompt specifications for settings actions."""

from pydantic import SecretStr

from openhands_cli.user_actions.prompt_spec import PromptSpec, PromptType, ValidationRule
from openhands_cli.tui.settings.constants import VERIFIED_PROVIDERS


# Settings type selection
SETTINGS_TYPE_SPEC = PromptSpec(
    question="Which settings would you like to modify?",
    prompt_type=PromptType.SELECTION,
    options=[
        "LLM (Basic)",
        "Go back",
    ],
    escapable=False
)

# LLM Provider selection
def create_llm_provider_spec() -> PromptSpec:
    """Create LLM provider selection spec."""
    options = VERIFIED_PROVIDERS.copy()
    options.append("Select another provider")
    
    return PromptSpec(
        question="Select LLM Provider:",
        prompt_type=PromptType.SELECTION,
        options=options,
        step_info="(Step 1/3)"
    )

# LLM Model selection (with autocomplete)
def create_llm_model_spec(models: list[str]) -> PromptSpec:
    """Create LLM model selection spec with autocomplete."""
    # Show top 4 models plus "Select another model" option
    display_options = models[:4] + ["Select another model"]
    
    return PromptSpec(
        question="Select LLM Model (TAB for options, CTRL-c to cancel):",
        prompt_type=PromptType.SELECTION,
        options=display_options,
        step_info="(Step 2/3)"
    )

# LLM Model autocomplete (for "Select another model" case)
def create_llm_model_autocomplete_spec(models: list[str]) -> PromptSpec:
    """Create LLM model autocomplete spec."""
    return PromptSpec(
        question="Type model id (TAB to complete, CTRL-c to cancel):",
        prompt_type=PromptType.TEXT_WITH_AUTOCOMPLETE,
        options=models,
        step_info="(Step 2/3)"
    )

# Provider selection (for "Select another provider" case)
PROVIDER_AUTOCOMPLETE_SPEC = PromptSpec(
    question="Select LLM Provider (TAB for options, CTRL-c to cancel):",
    prompt_type=PromptType.FREE_TEXT,
    step_info="(Step 1/3)",
    escapable=False
)

# API Key entry
def create_api_key_spec(existing_api_key: SecretStr | None = None) -> PromptSpec:
    """Create API key entry spec."""
    if existing_api_key:
        masked_key = existing_api_key.get_secret_value()[:3] + "***"
        question = f"Enter API Key [{masked_key}] (CTRL-c to cancel, ENTER to keep current, type new to change):"
        default_value = existing_api_key.get_secret_value()
    else:
        question = "Enter API Key (CTRL-c to cancel):"
        default_value = None
    
    return PromptSpec(
        question=question,
        prompt_type=PromptType.FREE_TEXT,
        step_info="(Step 3/3)",
        default_value=default_value,
        validation_rules=[
            ValidationRule(
                validator=lambda x: len(x.strip()) > 0,
                error_message="API key cannot be empty"
            )
        ]
    )

# Save settings confirmation
SAVE_SETTINGS_SPEC = PromptSpec(
    question="Save new settings? (They will take effect after restart)",
    prompt_type=PromptType.SELECTION,
    options=[
        "Yes, save",
        "No, discard"
    ]
)