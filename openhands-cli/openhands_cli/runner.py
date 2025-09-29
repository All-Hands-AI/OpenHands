from openhands.sdk import BaseConversation, Message
from openhands.sdk.security.confirmation_policy import (
    AlwaysConfirm,
    NeverConfirm,
    ConfirmRisky,
    ConfirmationPolicyBase
)
from openhands.sdk.conversation.state import AgentExecutionStatus, ConversationState
from prompt_toolkit import HTML, print_formatted_text

from openhands_cli.listeners.pause_listener import PauseListener, pause_listener
from openhands_cli.user_actions import ask_user_confirmation
from openhands_cli.user_actions.types import UserConfirmation


class ConversationRunner:
    """Handles the conversation state machine logic cleanly."""

    def __init__(self, conversation: BaseConversation):
        self.conversation = conversation

    @property
    def is_confirmation_mode_enabled(self):
        return self.conversation.confirmation_policy_active

    def toggle_confirmation_mode(self):
        if self.is_confirmation_mode_enabled:
            self.set_confirmation_policy(NeverConfirm())
        else:
            self.set_confirmation_policy(AlwaysConfirm())

    def set_confirmation_policy(self, confirmation_policy: ConfirmationPolicyBase) -> None:
        self.conversation.set_confirmation_policy(confirmation_policy)



    def _start_listener(self) -> None:
        self.listener = PauseListener(on_pause=self.conversation.pause)
        self.listener.start()

    def _print_run_status(self) -> None:
        print_formatted_text("")
        if self.conversation.state.agent_status == AgentExecutionStatus.PAUSED:
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

        if self.is_confirmation_mode_enabled:
            self._run_with_confirmation()
        else:
            self._run_without_confirmation()

    def _run_without_confirmation(self) -> None:
        with pause_listener(self.conversation):
            self.conversation.run()

    def _run_with_confirmation(self) -> None:
        # If agent was paused, resume with confirmation request
        if (
            self.conversation.state.agent_status
            == AgentExecutionStatus.WAITING_FOR_CONFIRMATION
        ):
            user_confirmation = self._handle_confirmation_request()
            if user_confirmation == UserConfirmation.DEFER:
                return

        while True:
            with pause_listener(self.conversation) as listener:
                self.conversation.run()

                if listener.is_paused():
                    break

            # In confirmation mode, agent either finishes or waits for user confirmation
            if self.conversation.state.agent_status == AgentExecutionStatus.FINISHED:
                break

            elif (
                self.conversation.state.agent_status
                == AgentExecutionStatus.WAITING_FOR_CONFIRMATION
            ):
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

        pending_actions = ConversationState.get_unmatched_actions(self.conversation.state.events)
        if not pending_actions:
            return UserConfirmation.ACCEPT



        result = ask_user_confirmation(
            pending_actions,
            isinstance(self.conversation.state.confirmation_policy, ConfirmRisky)
        )
        decision = result.decision
        policy_change = result.policy_change


        if decision == UserConfirmation.REJECT:
            self.conversation.reject_pending_actions(
                result.reason or "User rejected the actions"
            )
            return decision


        if decision == UserConfirmation.DEFER:
            self.conversation.pause()
            return decision


        if isinstance(policy_change, NeverConfirm):
            print_formatted_text(
                HTML(
                    "<yellow>Confirmation mode disabled. Agent will proceed without asking.</yellow>"
                )
            )
            self.set_confirmation_policy(policy_change)
            return decision



        if isinstance(policy_change, ConfirmRisky):
            print_formatted_text(
                HTML(
                    "<yellow>Security-based confirmation enabled. "
                    "LOW/MEDIUM risk actions will auto-confirm, HIGH risk actions will ask for confirmation.</yellow>"
                )
            )
            self.set_confirmation_policy(policy_change)
            return decision


        # Accept action without changing existing policies
        assert decision == UserConfirmation.ACCEPT
        return decision

