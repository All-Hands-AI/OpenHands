from prompt_toolkit import HTML, print_formatted_text

from openhands_cli.user_actions.types import UserConfirmation
from openhands_cli.user_actions.utils import cli_confirm, prompt_user


def ask_user_confirmation(pending_actions: list) -> tuple[UserConfirmation, str]:
    """Ask user to confirm pending actions.

    Args:
        pending_actions: List of pending actions from the agent

    Returns:
        Tuple of (UserConfirmation, reason) where reason is provided when rejecting with reason
    """

    reason = ""

    if not pending_actions:
        return UserConfirmation.ACCEPT, reason

    print_formatted_text(
        HTML(
            f"<yellow>🔍 Agent created {len(pending_actions)} action(s) and is waiting for confirmation:</yellow>"
        )
    )

    for i, action in enumerate(pending_actions, 1):
        tool_name = getattr(action, "tool_name", "[unknown tool]")
        print("tool name", tool_name)
        action_content = (
            str(getattr(action, "action", ""))[:100].replace("\n", " ")
            or "[unknown action]"
        )
        print("action_content", action_content)
        print_formatted_text(
            HTML(f"<grey>  {i}. {tool_name}: {action_content}...</grey>")
        )

    question = "Choose an option:"
    options = [
        "Yes, proceed",
        "No, reject (w/o reason)",
        "No, reject with reason",
        "Always proceed (don't ask again)",
    ]

    try:
        index = cli_confirm(question, options, escapable=True)
    except (EOFError, KeyboardInterrupt):
        print_formatted_text(HTML("\n<red>No input received; pausing agent.</red>"))
        return UserConfirmation.DEFER, reason

    if index == 0:
        return UserConfirmation.ACCEPT, reason
    elif index == 1:
        return UserConfirmation.REJECT, reason
    elif index == 2:
        reason, should_defer = prompt_user(
            "Please enter your reason for rejecting these actions: "
        )

        # If user pressed Ctrl+C or Ctrl+P during reason input, defer the action
        if should_defer:
            return UserConfirmation.DEFER, ""

        return UserConfirmation.REJECT, reason
    elif index == 3:
        return UserConfirmation.ALWAYS_ACCEPT, reason

    return UserConfirmation.REJECT, reason
