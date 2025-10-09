import os

from openhands.sdk import LLM, BaseConversation, LocalFileStore
from openhands.sdk.security.confirmation_policy import NeverConfirm
from openhands.tools.preset.default import get_default_agent
from prompt_toolkit import HTML, print_formatted_text
from prompt_toolkit.shortcuts import print_container
from prompt_toolkit.widgets import Frame, TextArea

from openhands_cli.llm_utils import get_llm_metadata
from openhands_cli.locations import AGENT_SETTINGS_PATH, PERSISTENCE_DIR
from openhands_cli.pt_style import COLOR_GREY
from openhands_cli.tui.settings.store import AgentStore
from openhands_cli.tui.utils import StepCounter
from openhands_cli.user_actions.settings_action import (
    SettingsType,
    choose_llm_model,
    choose_llm_provider,
    choose_memory_condensation,
    prompt_api_key,
    prompt_base_url,
    prompt_custom_model,
    save_settings_confirmation,
    settings_type_confirmation,
)


class SettingsScreen:
    def __init__(self, conversation: BaseConversation | None = None):
        self.file_store = LocalFileStore(PERSISTENCE_DIR)
        self.agent_store = AgentStore()
        self.conversation = conversation

    def display_settings(self) -> None:
        agent_spec = self.agent_store.load()
        if not agent_spec:
            return
        assert self.conversation is not None, (
            'Conversation must be set to display settings.'
        )

        llm = agent_spec.llm
        advanced_llm_settings = True if llm.base_url else False

        # Prepare labels and values based on settings
        labels_and_values = []
        if not advanced_llm_settings:
            # Attempt to determine provider, fallback if not directly available
            provider = llm.model.split('/')[0] if '/' in llm.model else 'Unknown'

            labels_and_values.extend(
                [
                    ('   LLM Provider', str(provider)),
                    ('   LLM Model', str(llm.model)),
                ]
            )
        else:
            labels_and_values.extend(
                [
                    ('   Custom Model', llm.model),
                    ('   Base URL', llm.base_url),
                ]
            )
        labels_and_values.extend(
            [
                ('   API Key', '********' if llm.api_key else 'Not Set'),
                (
                    '   Confirmation Mode',
                    'Enabled'
                    if self.conversation.is_confirmation_mode_active
                    else 'Disabled',
                ),
                (
                    '   Memory Condensation',
                    'Enabled' if agent_spec.condenser else 'Disabled',
                ),
                (
                    '   Configuration File',
                    os.path.join(PERSISTENCE_DIR, AGENT_SETTINGS_PATH),
                ),
            ]
        )

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
            f'{label + ":":<{max_label_width + 1}} {value:<}'  # Changed value alignment to left (<)
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

        self.configure_settings()

    def configure_settings(self, first_time=False):
        try:
            settings_type = settings_type_confirmation(first_time=first_time)
        except KeyboardInterrupt:
            return

        if settings_type == SettingsType.BASIC:
            self.handle_basic_settings()
        elif settings_type == SettingsType.ADVANCED:
            self.handle_advanced_settings()

    def handle_basic_settings(self):
        step_counter = StepCounter(3)
        try:
            provider = choose_llm_provider(step_counter, escapable=True)
            llm_model = choose_llm_model(step_counter, provider, escapable=True)
            api_key = prompt_api_key(
                step_counter,
                provider,
                self.conversation.state.agent.llm.api_key
                if self.conversation
                else None,
                escapable=True,
            )
            save_settings_confirmation()
        except KeyboardInterrupt:
            print_formatted_text(HTML('\n<red>Cancelled settings change.</red>'))
            return

        # Store the collected settings for persistence
        self._save_llm_settings(f'{provider}/{llm_model}', api_key)

    def handle_advanced_settings(self, escapable=True):
        """Handle advanced settings configuration with clean step-by-step flow."""
        step_counter = StepCounter(4)
        try:
            custom_model = prompt_custom_model(step_counter)
            base_url = prompt_base_url(step_counter)
            api_key = prompt_api_key(
                step_counter,
                custom_model.split('/')[0] if len(custom_model.split('/')) > 1 else '',
                self.conversation.agent.llm.api_key if self.conversation else None,
                escapable=escapable,
            )
            memory_condensation = choose_memory_condensation(step_counter)

            # Confirm save
            save_settings_confirmation()
        except KeyboardInterrupt:
            print_formatted_text(HTML('\n<red>Cancelled settings change.</red>'))
            return

        # Store the collected settings for persistence
        self._save_advanced_settings(
            custom_model, base_url, api_key, memory_condensation
        )

    def _save_llm_settings(self, model, api_key, base_url: str | None = None) -> None:
        llm = LLM(
            model=model,
            api_key=api_key,
            base_url=base_url,
            service_id='agent',
            metadata=get_llm_metadata(model_name=model, llm_type='agent'),
        )

        agent = self.agent_store.load()
        if not agent:
            agent = get_default_agent(llm=llm, cli_mode=True)

        agent = agent.model_copy(update={'llm': llm})
        self.agent_store.save(agent)

    def _save_advanced_settings(
        self, custom_model: str, base_url: str, api_key: str, memory_condensation: bool
    ):
        self._save_llm_settings(custom_model, api_key, base_url=base_url)

        agent_spec = self.agent_store.load()
        if not agent_spec:
            return

        if not memory_condensation:
            agent_spec.model_copy(update={'condenser': None})

        self.agent_store.save(agent_spec)
