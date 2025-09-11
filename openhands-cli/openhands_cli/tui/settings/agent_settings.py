"""Agent settings configuration UI."""

from ...settings.constants import SUPPORTED_AGENTS
from ...settings.models import AgentSettings
from ..components.settings_display import SettingsDisplay
from ..components.input_handlers import InputHandler


class AgentSettingsHandler:
    """Handler for agent settings configuration."""

    def __init__(self):
        """Initialize agent settings handler."""
        self.display = SettingsDisplay()
        self.input = InputHandler()

    def display_current_settings(self, settings: AgentSettings) -> None:
        """Display current agent settings."""
        self.display.settings_group('Agent Configuration', {
            'Agent Type': settings.agent_type,
            'Confirmation Mode': settings.confirmation_mode
        })

    def configure_agent_type(self, current: str) -> str:
        """Configure agent type selection."""
        self.display.subsection_header('Select Agent Type')
        
        choices = SUPPORTED_AGENTS + ['Other (specify)']
        selected_idx = self.input.get_choice(
            'Choose agent type:',
            choices=choices,
            current=current
        )
        
        if selected_idx == len(choices) - 1:  # "Other" selected
            return self.input.get_custom_value(
                'Enter custom agent type: ',
                current=current
            ) or current
        
        return choices[selected_idx]

    def configure_confirmation_mode(self, current: bool) -> bool:
        """Configure confirmation mode setting."""
        self.display.subsection_header('Confirmation Mode')
        
        return self.input.get_boolean_choice(
            'Confirmation Mode:',
            current=current
        )

    def configure(self, current_settings: AgentSettings) -> AgentSettings:
        """Configure all agent settings."""
        self.display.section_header('Configure Agent Settings', '🤖')
        
        # Display current settings
        self.display_current_settings(current_settings)
        print_formatted_text('')
        
        # Configure each setting
        agent_type = self.configure_agent_type(current_settings.agent_type)
        print_formatted_text('')
        
        confirmation_mode = self.configure_confirmation_mode(
            current_settings.confirmation_mode
        )
        
        # Create new settings
        new_settings = AgentSettings(
            agent_type=agent_type,
            confirmation_mode=confirmation_mode
        )
        
        self.display.success_message('Agent settings updated successfully!')
        return new_settings