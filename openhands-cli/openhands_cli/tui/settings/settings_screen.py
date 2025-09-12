from openhands.sdk import Conversation
from openhands_cli.user_actions import settings_type_confirmation
from openhands_cli.user_actions.settings_action import SettingsType, choose_llm_provider, save_settings_confirmation, specify_api_key
from openhands_cli.user_actions.types import UserConfirmation
from openhands.sdk import Conversation
from prompt_toolkit.widgets import Frame, TextArea

from openhands_cli.pt_style import COLOR_GREY
from prompt_toolkit.shortcuts import print_container


class SettingsScreen:
    def __init__(self, conversation: Conversation):
        self.conversation = conversation


    def display_settings(self) -> None:
        llm = self.conversation.agent.llm
        advanced_llm_settings = True if llm.base_url else False

        # Prepare labels and values based on settings
        labels_and_values = []
        if not advanced_llm_settings:
            # Attempt to determine provider, fallback if not directly available
            provider = llm.model.split('/')[0] if '/' in llm.model else 'Unknown',

            labels_and_values.extend(
                [
                    ('   LLM Provider', str(provider)),
                    ('   LLM Model', str(llm.model)),
                    ('   API Key', '********' if llm.api_key else 'Not Set'),
                ]
            )
        else:
            labels_and_values.extend(
                [
                    ('   Custom Model', str(llm.model)),
                    ('   Base URL', str(llm.base_url)),
                    ('   API Key', '********' if llm.api_key else 'Not Set'),
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


    def configure_settings(self):
        confirmation, settings_type = settings_type_confirmation()
        if confirmation == UserConfirmation.REJECT:
            return


        if settings_type == SettingsType.BASIC:
            self.handle_basic_settings()


    def handle_basic_settings(self):
        provider = choose_llm_provider()
        api_key = specify_api_key(self.conversation.agent.llm.api_key)

        if not api_key:
            return

        confirmation = save_settings_confirmation()
        if confirmation == UserConfirmation.REJECT:
            return

        self.reconfigure_conversation_settings()


    def reconfigure_conversation_settings(self):
        pass



