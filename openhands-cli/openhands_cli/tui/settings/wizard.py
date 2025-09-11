"""First-time setup wizard for OpenHands CLI."""

from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import HTML

from openhands.core.config.llm_config import LLMConfig
from ...settings.manager import CLISettings
from ..components.settings_display import SettingsDisplay
from ..components.input_handlers import InputHandler


class SetupWizard:
    """First-time setup wizard for OpenHands CLI."""

    def __init__(self):
        """Initialize setup wizard."""
        self.display = SettingsDisplay()
        self.input = InputHandler()
        self.settings = CLISettings()

    def _welcome(self) -> None:
        """Display welcome message."""
        print_formatted_text('')
        self.display.section_header('Welcome to OpenHands CLI! 👋')
        print_formatted_text(HTML(
            '<yellow>This wizard will help you configure your settings.</yellow>'
        ))
        print_formatted_text('')

    def _configure_model(self) -> str:
        """Configure LLM model."""
        self.display.subsection_header('Step 1: Select LLM Model')
        print_formatted_text(HTML(
            '<grey>Choose the language model to use for agent interactions.</grey>'
        ))
        print_formatted_text('')
        
        choices = [
            'gpt-4-turbo-preview',
            'gpt-4',
            'gpt-3.5-turbo',
            'claude-3-opus-20240229',
            'claude-3-sonnet-20240229',
            'claude-3-haiku-20240307',
            'Other (specify)'
        ]
        selected_idx = self.input.get_choice(
            'Choose a model:',
            choices=choices,
            current=None
        )
        
        if selected_idx == len(choices) - 1:  # "Other" selected
            return self.input.get_custom_value(
                'Enter custom model name: ',
                current=None
            )
        
        return choices[selected_idx]

    def _configure_api_key(self) -> str:
        """Configure API key."""
        self.display.subsection_header('Step 2: Configure API Key')
        print_formatted_text(HTML(
            '<grey>Enter your API key for the selected model.</grey>'
        ))
        print_formatted_text('')
        
        value, _ = self.input.get_secret_value(
            'Enter API Key:',
            current=None
        )
        
        return value

    def _configure_base_url(self) -> str | None:
        """Configure base URL."""
        self.display.subsection_header('Step 3: Configure Base URL (Optional)')
        print_formatted_text(HTML(
            '<grey>Enter a custom base URL if needed (leave empty for default).</grey>'
        ))
        print_formatted_text('')
        
        value = self.input.get_custom_value(
            'Enter Base URL: ',
            current=None
        )
        
        return value if value else None

    def _configure_temperature(self) -> float:
        """Configure temperature."""
        self.display.subsection_header('Step 4: Configure Temperature')
        print_formatted_text(HTML(
            '<grey>Set the temperature for model responses (0.0 - 1.0).</grey>'
        ))
        print_formatted_text(HTML(
            '<grey>Lower values make responses more focused, higher values more creative.</grey>'
        ))
        print_formatted_text('')
        
        return float(self.input.get_custom_value(
            'Enter temperature (0.0 - 1.0): ',
            current='0.7',
            validator=lambda x: 0.0 <= float(x) <= 1.0
        ))

    def _configure_top_p(self) -> float:
        """Configure top p."""
        self.display.subsection_header('Step 5: Configure Top P')
        print_formatted_text(HTML(
            '<grey>Set the top p value for model responses (0.0 - 1.0).</grey>'
        ))
        print_formatted_text(HTML(
            '<grey>Controls diversity of responses. Lower values make responses more focused.</grey>'
        ))
        print_formatted_text('')
        
        return float(self.input.get_custom_value(
            'Enter top p (0.0 - 1.0): ',
            current='1.0',
            validator=lambda x: 0.0 <= float(x) <= 1.0
        ))

    def _configure_max_tokens(self) -> int | None:
        """Configure max output tokens."""
        self.display.subsection_header('Step 6: Configure Max Output Tokens (Optional)')
        print_formatted_text(HTML(
            '<grey>Set maximum number of tokens in model responses.</grey>'
        ))
        print_formatted_text(HTML(
            '<grey>Leave empty for no limit. Higher values allow longer responses.</grey>'
        ))
        print_formatted_text('')
        
        value = self.input.get_custom_value(
            'Enter max output tokens (leave empty for no limit): ',
            current='',
            validator=lambda x: not x or int(x) > 0
        )
        
        return int(value) if value else None

    def _save_settings(self, config: LLMConfig) -> None:
        """Save settings and show completion message."""
        self.settings.update_llm(config)
        
        print_formatted_text('')
        self.display.section_header('Setup Complete! 🎉')
        print_formatted_text(HTML(
            '<green>Your settings have been saved successfully.</green>'
        ))
        print_formatted_text('')
        print_formatted_text(HTML(
            '<grey>You can update these settings anytime using the /settings command.</grey>'
        ))
        print_formatted_text('')

    def run(self) -> None:
        """Run the setup wizard."""
        self._welcome()
        
        # Configure each setting
        model = self._configure_model()
        print_formatted_text('')
        
        api_key = self._configure_api_key()
        print_formatted_text('')
        
        base_url = self._configure_base_url()
        print_formatted_text('')
        
        temperature = self._configure_temperature()
        print_formatted_text('')
        
        top_p = self._configure_top_p()
        print_formatted_text('')
        
        max_output_tokens = self._configure_max_tokens()
        
        # Create and save settings
        config = LLMConfig(
            model=model,
            api_key=api_key,
            base_url=base_url,
            temperature=temperature,
            top_p=top_p,
            max_output_tokens=max_output_tokens
        )
        
        self._save_settings(config)