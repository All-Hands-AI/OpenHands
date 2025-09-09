from openhands.sdk import Conversation, Message
from openhands.sdk.event.utils import get_unmatched_actions
from prompt_toolkit import HTML, print_formatted_text

from openhands_cli.listeners.pause_listener import PauseListener, pause_listener
from openhands_cli.user_actions import ask_user_confirmation
from openhands_cli.user_actions.types import UserConfirmation


class ConversationRunner:
    """Handles the conversation state machine logic cleanly."""

    def __init__(self, conversation: Conversation):
        self.conversation = conversation
        self.confirmation_mode = False

    def set_confirmation_mode(self, confirmation_mode: bool) -> None:
        self.confirmation_mode = confirmation_mode
        self.conversation.set_confirmation_mode(confirmation_mode)

    def _start_listener(self) -> None:
        self.listener = PauseListener(on_pause=self.conversation.pause)
        self.listener.start()

    def _print_run_status(self) -> None:
        print_formatted_text("")
        if self.conversation.state.agent_paused:
            print_formatted_text(
                HTML(
                    "<yellow>Resuming paused conversation...</yellow><grey> (Press Ctrl-P to pause)</grey>"
                )
            )

        else:
            print_formatted_text(
                HTML(
                    "<yellow>Agent running...</yellow><grey> (Press Ctrl-P to pause)</grey>"
                )
            )
        print_formatted_text("")

    def process_message(self, message: Message | None) -> None:
        """Process a user message through the conversation.

        Args:
            message: The user message to process
        """

        self._print_run_status()

        # Send message to conversation
        if message:
            self.conversation.send_message(message)

        if self.confirmation_mode:
            self._run_with_confirmation()
        else:
            self._run_without_confirmation()

    def _run_without_confirmation(self) -> None:
        with pause_listener(self.conversation):
            self.conversation.run()

    def _run_with_confirmation(self) -> None:
        # If agent was paused, resume with confirmation request
        if self.conversation.state.agent_waiting_for_confirmation:
            user_confirmation = self._handle_confirmation_request()
            if user_confirmation == UserConfirmation.DEFER:
                return

        while True:
            with pause_listener(self.conversation) as listener:
                self.conversation.run()

                if listener.is_paused():
                    break

            # In confirmation mode, agent either finishes or waits for user confirmation
            if self.conversation.state.agent_finished:
                break

            elif self.conversation.state.agent_waiting_for_confirmation:
                user_confirmation = self._handle_confirmation_request()
                if user_confirmation == UserConfirmation.DEFER:
                    return

            else:
                raise Exception("Infinite loop")

    def _handle_confirmation_request(self) -> UserConfirmation:
        """Handle confirmation request from user.

        Returns:
            UserConfirmation indicating the user's choice
        """
        pending_actions = get_unmatched_actions(self.conversation.state.events)

        if pending_actions:
            user_confirmation, reason = ask_user_confirmation(pending_actions)
            if user_confirmation == UserConfirmation.REJECT:
                self.conversation.reject_pending_actions(
                    reason or "User rejected the actions"
                )
            elif user_confirmation == UserConfirmation.DEFER:
                self.conversation.pause()
            elif user_confirmation == UserConfirmation.ALWAYS_ACCEPT:
                # Disable confirmation mode when user selects "Always proceed"
                print_formatted_text(
                    HTML(
                        "<yellow>Confirmation mode disabled. Agent will proceed without asking.</yellow>"
                    )
                )
                self.set_confirmation_mode(False)

            return user_confirmation

        return UserConfirmation.ACCEPT
