import html
from prompt_toolkit import HTML, print_formatted_text

from openhands.sdk.security.confirmation_policy import (
    ConfirmRisky,
    NeverConfirm,
    SecurityRisk,
)
from openhands_cli.user_actions.types import ConfirmationResult, UserConfirmation
from openhands_cli.user_actions.utils import cli_confirm, cli_text_input


def ask_user_confirmation(
    pending_actions: list, using_risk_based_policy: bool = False
) -> ConfirmationResult:
    """Ask user to confirm pending actions.

    Args:
        pending_actions: List of pending actions from the agent

    Returns:
        ConfirmationResult with decision, optional policy_change, and reason
    """

    if not pending_actions:
        return ConfirmationResult(decision=UserConfirmation.ACCEPT)

    print_formatted_text(
        HTML(
            f'<yellow>🔍 Agent created {len(pending_actions)} action(s) and is waiting for confirmation:</yellow>'
        )
    )

    for i, action in enumerate(pending_actions, 1):
        tool_name = getattr(action, 'tool_name', '[unknown tool]')
        action_content = (
            str(getattr(action, 'action', ''))[:100].replace('\n', ' ')
            or '[unknown action]'
        )
        print_formatted_text(
            HTML(f'<grey>  {i}. {tool_name}: {html.escape(action_content)}...</grey>')
        )

    question = 'Choose an option:'
    options = [
        'Yes, proceed',
        'No, reject (w/o reason)',
        'No, reject with reason',
        "Always proceed (don't ask again)",
    ]

    if not using_risk_based_policy:
        options.append('Auto-confirm LOW/MEDIUM risk, ask for HIGH risk')

    try:
        index = cli_confirm(question, options, escapable=True)
    except (EOFError, KeyboardInterrupt):
        print_formatted_text(HTML('\n<red>No input received; pausing agent.</red>'))
        return ConfirmationResult(decision=UserConfirmation.DEFER)

    if index == 0:
        return ConfirmationResult(decision=UserConfirmation.ACCEPT)
    elif index == 1:
        return ConfirmationResult(decision=UserConfirmation.REJECT)
    elif index == 2:
        try:
            reason_result = cli_text_input(
                'Please enter your reason for rejecting these actions: '
            )
        except Exception:
            return ConfirmationResult(decision=UserConfirmation.DEFER)

        # Support both string return and (reason, cancelled) tuple for tests
        cancelled = False
        if isinstance(reason_result, tuple) and len(reason_result) >= 1:
            reason = reason_result[0] or ''
            cancelled = bool(reason_result[1]) if len(reason_result) > 1 else False
        else:
            reason = str(reason_result or '').strip()

        if cancelled:
            return ConfirmationResult(decision=UserConfirmation.DEFER)

        return ConfirmationResult(decision=UserConfirmation.REJECT, reason=reason)
    elif index == 3:
        return ConfirmationResult(
            decision=UserConfirmation.ACCEPT, policy_change=NeverConfirm()
        )
    elif index == 4:
        return ConfirmationResult(
            decision=UserConfirmation.ACCEPT,
            policy_change=ConfirmRisky(threshold=SecurityRisk.HIGH),
        )

    return ConfirmationResult(decision=UserConfirmation.REJECT)
