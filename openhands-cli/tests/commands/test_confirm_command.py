#!/usr/bin/env python3

from unittest.mock import MagicMock, patch, call
import pytest

from openhands_cli.runner import ConversationRunner
from openhands.sdk.security.confirmation_policy import AlwaysConfirm, NeverConfirm

CONV_ID = "test-conversation-id"


# ---------- Helpers ----------
def make_conv(enabled: bool) -> MagicMock:
    """Return a conversation mock in enabled/disabled confirmation mode."""
    m = MagicMock()
    m.id = CONV_ID
    m.agent.security_analyzer = MagicMock() if enabled else None
    m.confirmation_policy_active = enabled
    m.is_confirmation_mode_active = enabled
    return m


@pytest.fixture
def runner_disabled() -> ConversationRunner:
    """Runner starting with confirmation mode disabled."""
    return ConversationRunner(make_conv(enabled=False))


@pytest.fixture
def runner_enabled() -> ConversationRunner:
    """Runner starting with confirmation mode enabled."""
    return ConversationRunner(make_conv(enabled=True))


# ---------- Core toggle behavior (parametrized) ----------
@pytest.mark.parametrize(
    "start_enabled, include_security_analyzer, expected_enabled, expected_policy_cls",
    [
        # disabled -> enable
        (False, True, True, AlwaysConfirm),
        # enabled -> disable
        (True, False, False, NeverConfirm),
    ],
)
def test_toggle_confirmation_mode_transitions(
    start_enabled, include_security_analyzer, expected_enabled, expected_policy_cls
):
    # Arrange: pick starting runner & prepare the target conversation
    runner = ConversationRunner(make_conv(enabled=start_enabled))
    target_conv = make_conv(enabled=expected_enabled)

    with patch("openhands_cli.runner.setup_conversation", return_value=target_conv) as mock_setup:
        # Act
        runner.toggle_confirmation_mode()

        # Assert state
        assert runner.is_confirmation_mode_active is expected_enabled
        assert runner.conversation is target_conv

        # Assert setup called with same conversation ID + correct analyzer flag
        mock_setup.assert_called_once_with(CONV_ID, include_security_analyzer=include_security_analyzer)

        # Assert policy applied to the *new* conversation
        target_conv.set_confirmation_policy.assert_called_once()
        assert isinstance(target_conv.set_confirmation_policy.call_args.args[0], expected_policy_cls)


# ---------- Conversation ID is preserved across multiple toggles ----------
def test_maintains_conversation_id_across_toggles(runner_disabled: ConversationRunner):
    enabled_conv = make_conv(enabled=True)
    disabled_conv = make_conv(enabled=False)

    with patch("openhands_cli.runner.setup_conversation") as mock_setup:
        mock_setup.side_effect = [enabled_conv, disabled_conv]

        # Toggle on, then off
        runner_disabled.toggle_confirmation_mode()
        runner_disabled.toggle_confirmation_mode()

        assert runner_disabled.conversation.id == CONV_ID
        mock_setup.assert_has_calls(
            [
                call(CONV_ID, include_security_analyzer=True),
                call(CONV_ID, include_security_analyzer=False),
            ],
            any_order=False,
        )


# ---------- Idempotency under rapid alternating toggles ----------
def test_rapid_alternating_toggles_produce_expected_states(runner_disabled: ConversationRunner):
    enabled_conv = make_conv(enabled=True)
    disabled_conv = make_conv(enabled=False)

    with patch("openhands_cli.runner.setup_conversation") as mock_setup:
        mock_setup.side_effect = [enabled_conv, disabled_conv, enabled_conv, disabled_conv]

        # Start disabled
        assert runner_disabled.is_confirmation_mode_active is False

        # Enable, Disable, Enable, Disable
        runner_disabled.toggle_confirmation_mode()
        assert runner_disabled.is_confirmation_mode_active is True

        runner_disabled.toggle_confirmation_mode()
        assert runner_disabled.is_confirmation_mode_active is False

        runner_disabled.toggle_confirmation_mode()
        assert runner_disabled.is_confirmation_mode_active is True

        runner_disabled.toggle_confirmation_mode()
        assert runner_disabled.is_confirmation_mode_active is False

        mock_setup.assert_has_calls(
            [
                call(CONV_ID, include_security_analyzer=True),
                call(CONV_ID, include_security_analyzer=False),
                call(CONV_ID, include_security_analyzer=True),
                call(CONV_ID, include_security_analyzer=False),
            ],
            any_order=False,
        )
