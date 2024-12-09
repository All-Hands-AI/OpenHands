import json
import re
from typing import Any, TypedDict, cast

from openhands.controller.state.state import State
from openhands.core.logger import openhands_logger as logger
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


# Produce the command string for the `annotate-execution-points` command.
def command_annotate_execution_points(
    thought: str, is_workspace_repo: bool
) -> ReplayCmdRunAction:
    # NOTE: For the resolver, the workdir path is the repo path.
    #       In that case, we should not append the repo name to the path.
    is_repo_flag = ' -i' if is_workspace_repo else ''
    # If the workspace is the repo, it should already have been hard reset.
    force_flag = ' -f' if not is_workspace_repo else ''
    command = f'"annotate-execution-points" -w "$(pwd)"{is_repo_flag}{force_flag}'
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
    if enhance_action_id is None:
        # 1. Get current user prompt.
        latest_user_message = state.get_last_user_message()
        if latest_user_message:
            logger.info(f'[REPLAY] latest_user_message id is {latest_user_message.id}')
            # 2. Check if it has a recordingId.
            recording_id = scan_recording_id(latest_user_message.content)
            if recording_id:
                # 3. Analyze recording and start the enhancement action.
                logger.info(
                    f'[REPLAY] Enhancing prompt for Replay recording "{recording_id}"...'
                )
                state.extra_data['replay_enhance_prompt_id'] = latest_user_message.id
                logger.info('[REPLAY] stored latest_user_message id in state')
                return command_annotate_execution_points(
                    latest_user_message.content, is_workspace_repo
                )
    return None


class AnnotatedLocation(TypedDict, total=False):
    filePath: str
    line: int


class AnnotateResult(TypedDict, total=False):
    status: str
    point: str
    commentText: str | None
    annotatedRepo: str
    annotatedLocations: list[AnnotatedLocation]
    pointLocation: str | None


class ReplayCommandResult(TypedDict, total=False):
    # TODO: Use generics instead of `Any`. We currently cannot that because it raised an error saying that generics are not yet supported. Not sure why.
    result: Any | None
    error: str | None
    errorDetails: str | None


def safe_parse_json(text: str):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def handle_replay_enhance_observation(
    state: State, observation: ReplayCmdOutputObservation
) -> bool:
    enhance_action_id = state.extra_data.get('replay_enhance_prompt_id')
    if enhance_action_id is not None:
        user_message: MessageAction | None = next(
            (
                m
                for m in state.history
                if m.id == enhance_action_id and isinstance(m, MessageAction)
            ),
            None,
        )
        assert user_message

        output: ReplayCommandResult = safe_parse_json(observation.content)
        if output and output.get('result'):
            original_prompt = user_message.content
            result: AnnotateResult = cast(AnnotateResult, output.get('result', {}))
            annotated_repo_path = result.get('annotatedRepo', '')
            comment_text = result.get('commentText', '')
            react_component_name = result.get('reactComponentName', '')
            # start_location = result.get('startLocation', '')
            start_name = result.get('startName', '')

            # TODO: Move this to a prompt template file.
            if react_component_name:
                enhancement = f'There is a change needed to the {react_component_name} component.\n'
            else:
                enhancement = f'There is a change needed in {annotated_repo_path}:\n'
            enhancement += f'{comment_text}\n\n'
            enhancement += 'Reproduction information from a recording of the problem is available in source comments.\n'
            enhancement += f'The bug was reported at {start_name}. Start your investigation there. Then keep searching for related `reproduction step` comments.\n'

            enhancement += '<IMPORTANT>\n'
            enhancement += (
                'USE THESE COMMENTS TO GET A BETTER UNDERSTANDING OF THE PROBLEM.\n'
            )
            enhancement += '</IMPORTANT>\n'

            # Enhance:
            user_message.content = f'{enhancement}\n\n{original_prompt}'
            # user_message.content = enhancement
            logger.info(f'[REPLAY] Enhanced user prompt:\n{user_message.content}')
            return True
        else:
            logger.warning(
                f'DDBG Replay command did not return a result. Instead it returned: {str(output)}'
            )

    return False
