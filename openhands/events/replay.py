import re

from openhands.controller.state.state import State
from openhands.core.logger import openhands_logger as logger
from openhands.events.action.action import Action
from openhands.events.action.message import MessageAction
from openhands.events.action.replay import ReplayCmdRunAction


def scan_recording_id(issue: str) -> str | None:
    match = re.search(r'\.replay\.io\/recording\/([a-zA-Z0-9-]+)', issue)
    if not match:
        return None

    id_maybe_with_title = match.group(1)
    match2 = re.search(r'^.*?--([a-zA-Z0-9-]+)$', id_maybe_with_title)

    if match2:
        return match2.group(1)
    return id_maybe_with_title


def command_annotate_execution_points(
    thought: str, is_workspace_repo: bool
) -> ReplayCmdRunAction:
    # NOTE: For the resolver, the workdir path is the repo path.
    #       In that case, we should not append the repo name to the path.
    appendRepoNameToPath = ' -i' if is_workspace_repo else ''
    command = f'"annotate-execution-points" -w "$(pwd)"{appendRepoNameToPath}'
    action = ReplayCmdRunAction(
        thought=thought,
        command=command,
        # NOTE: The command will be followed by a file containing the thought.
        file_arguments=[thought],
        keep_prompt=False,
        # hidden=True, # The hidden implementation causes problems, so we added replay stuff to `filter_out` instead.
        in_workspace_dir=True,
    )
    return action


def replay_enhance_action(state: State, is_workspace_repo: bool) -> Action | None:
    enhance_action_id = state.extra_data.get('replay_enhance_prompt_id')
    if not enhance_action_id:
        # 1. Get current user prompt.
        latest_user_message = state.get_last_user_message()
        if latest_user_message:
            logger.info(f'[REPLAY] latest_user_message id is {latest_user_message.id}')
            # 2. Check if it has a recordingId.
            recording_id = scan_recording_id(latest_user_message.content)
            if recording_id:
                # 3. Analyze recording and, ultimately, enhance prompt.
                state.extra_data['replay_enhance_prompt_id'] = latest_user_message.id
                logger.info('[REPLAY] stored latest_user_message id in state')
                return command_annotate_execution_points(
                    latest_user_message.content, is_workspace_repo
                )
    return None


def handle_replay_enhance_observation(
    state: State,
    # observation: ReplayCmdOutputObservation
):
    enhance_action_id = state.extra_data.get('replay_enhance_prompt_id')
    if enhance_action_id is not None:
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

        # Enhance user action with observation result:
        user_message.content = f'{user_message.content}\n\nNOTEs to agent:\n* The repository has already been cloned and preprocessed.\n* The provided replay recording has been used to annotate the code.'
