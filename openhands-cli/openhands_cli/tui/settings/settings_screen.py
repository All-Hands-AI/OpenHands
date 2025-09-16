from openhands_cli.locations import LLM_SETTINGS_PATH
from openhands_cli.user_actions.settings_action import (
    SettingsType,
    choose_llm_model,
    choose_llm_provider,
    prompt_api_key,
    save_settings_confirmation,
    settings_type_confirmation,
    prompt_custom_model,
    prompt_base_url,
    prompt_advanced_api_key,
    choose_agent,
    choose_confirmation_mode,
    choose_memory_condensation,
)
from openhands_cli.tui.utils import StepCounter
from prompt_toolkit import HTML, print_formatted_text
from openhands.sdk import Conversation, LLM
from pydantic import SecretStr
from prompt_toolkit.shortcuts import print_container
from prompt_toolkit.widgets import Frame, TextArea

from openhands_cli.pt_style import COLOR_GREY


class SettingsScreen:
    def __init__(self, conversation: Conversation | None = None):
        self.conversation = conversation

    def display_settings(self) -> None:
        if not self.conversation:
            return

        llm = self.conversation.agent.llm
        advanced_llm_settings = True if llm.base_url else False

        # Prepare labels and values based on settings
        labels_and_values = []
        if not advanced_llm_settings:
            # Attempt to determine provider, fallback if not directly available
            provider = llm.model.split('/')[0] if '/' in llm.model else 'Unknown'

            labels_and_values.extend(
                [
                    ("   LLM Provider", str(provider)),
                    ("   LLM Model", str(llm.model)),
                    ("   API Key", "********" if llm.api_key else "Not Set"),
                ]
            )
        else:
            labels_and_values.extend(
                [
                    ("   LLM Provider", "openhands"),
                    ("   LLM Model", str(llm.model)),
                    ("   API Key", "********" if llm.api_key else "Not Set"),
                ]
            )

        # Add common settings that are always displayed
        labels_and_values.extend([
            ("   Agent", "TomCodeActAgent"),  # Default agent type for now
            ("   Confirmation Mode", "Enabled" if self.conversation.state.confirmation_mode else "Disabled"),
            ("   Memory Condensation", "Enabled"),  # Default for now
            ("   Search API Key", "Not Set"),  # Placeholder for search API
            ("   Configuration File", "~/.openhands/settings.json"),
        ])

        # Calculate max widths for alignment
        # Ensure values are strings for len() calculation
        str_labels_and_values = [
            (label, str(value)) for label, value in labels_and_values
        ]
        max_label_width = (
            max(len(label) for label, _ in str_labels_and_values)
            if str_labels_and_values
            else 0
        )

        # Construct the summary text with aligned columns
        settings_lines = [
            f"{label + ':':<{max_label_width + 1}} {value:<}"  # Changed value alignment to left (<)
            for label, value in str_labels_and_values
        ]
        settings_text = "\n".join(settings_lines)

        container = Frame(
            TextArea(
                text=settings_text,
                read_only=True,
                style=COLOR_GREY,
                wrap_lines=True,
            ),
            title="Settings",
            style=f"fg:{COLOR_GREY}",
        )

        print_container(container)

        self.configure_settings()

    def configure_settings(self):
        try:
            settings_type = settings_type_confirmation()
        except KeyboardInterrupt:
            return

        if settings_type == SettingsType.BASIC:
            self.handle_basic_settings()
        elif settings_type == SettingsType.ADVANCED:
            self.handle_advanced_settings()

    def handle_basic_settings(self, escapable=True):
        step_counter = StepCounter(3)
        try:
            provider = choose_llm_provider(step_counter, escapable=escapable)
            llm_model = choose_llm_model(step_counter, provider, escapable=escapable)
            api_key = prompt_api_key(
                step_counter,
                provider,
                self.conversation.agent.llm.api_key if self.conversation else None,
                escapable=escapable
            )
            save_settings_confirmation()
        except KeyboardInterrupt:
            print_formatted_text(HTML('\n<red>Cancelled settings change.</red>'))
            return

        # Store the collected settings for persistence
        self._save_llm_settings(provider, llm_model, api_key)

    def handle_advanced_settings(self, escapable=True):
        """Handle advanced settings configuration with clean step-by-step flow."""
        step_counter = StepCounter(6)
        try:
            custom_model = prompt_custom_model(step_counter)
            base_url = prompt_base_url(step_counter)
            api_key = prompt_api_key(
                step_counter,
                custom_model.split('/')[0] if len(custom_model.split('/')) > 1 else '',
                self.conversation.agent.llm.api_key if self.conversation else None,
                escapable=escapable
            )
            agent = choose_agent(step_counter)
            memory_condensation = choose_memory_condensation(step_counter)

            # Confirm save
            save_settings_confirmation()
        except KeyboardInterrupt:
            print_formatted_text(HTML('\n<red>Cancelled settings change.</red>'))
            return

        # Store the collected settings for persistence
        self._save_advanced_settings(
            custom_model,
            base_url,
            api_key,
            agent,
            memory_condensation
        )

    def _save_llm_settings(
        self, provider: str, model: str, api_key: str
    ):
        """Update conversation settings with new values."""
        llm = LLM(model=f"{provider}/{model}", api_key=SecretStr(api_key))
        llm.store_to_json(LLM_SETTINGS_PATH)

    def _save_advanced_settings(
        self,
        custom_model: str,
        base_url: str,
        api_key: str,
        agent: str,
        confirmation_mode: bool,
        memory_condensation: bool
    ):
        # TODO: figure out agent configuration
        pass
