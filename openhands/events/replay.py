import re

from openhands.controller.state.state import State
from openhands.events.action.action import Action
from openhands.events.action.message import MessageAction
from openhands.events.action.replay import ReplayCmdRunAction
from openhands.events.observation.replay import ReplayCmdOutputObservation


def scan_recording_id(issue: str) -> str | None:
    match = re.search(r'\.replay\.io\/recording\/([a-zA-Z0-9-]+)', issue)
    if not match:
        return None

    id_maybe_with_title = match.group(1)
    match2 = re.search(r'^.*?--([a-zA-Z0-9-]+)$', id_maybe_with_title)

    if match2:
        return match2.group(1)
    return id_maybe_with_title


def command_annotate_execution_points(thought: str) -> ReplayCmdRunAction:
    # NOTE: In resolve_issue, the workspace base dir in AppConfig already points at the repo.
    #          -> in [output_dir, 'workspace', f'{issue_handler.issue_type}_{issue.number}']
    command = '"annotate-execution-points" "$(pwd)"'  # followed by file_arguments.
    action = ReplayCmdRunAction(
        thought=thought,
        command=command,
        file_arguments=[thought],
        keep_prompt=False,
        hidden=True,
        in_workspace_dir=True,
    )
    return action


def replay_enhance_action(state: State) -> Action | None:
    latest_user_message = state.get_last_user_message()
    if latest_user_message and not state.extra_data['replay_enhance_prompt_id']:
        recording_id = scan_recording_id(latest_user_message.content)
        if recording_id:
            state.extra_data['replay_enhance_prompt_id'] = latest_user_message.id
            return command_annotate_execution_points(latest_user_message.content)
    return None


def handle_replay_enhance_observation(
    state: State, observation: ReplayCmdOutputObservation
):
    enhance_action_id = state.extra_data['replay_enhance_prompt_id']
    assert enhance_action_id
    user_message: MessageAction | None = next(
        (
            m
            for m in state.history
            if m.id == enhance_action_id and isinstance(m, MessageAction)
        ),
        None,
    )
    assert user_message
    assert user_message.id == observation.cause

    # Enhance user action with observation result:
    # TODO: Append firstComment text.
    # user_message.content = f"{user_message.content}\n\n{observation.content}"
