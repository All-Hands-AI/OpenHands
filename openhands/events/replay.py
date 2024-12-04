import json
import re
from typing import Any, TypedDict

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
            # 2. Check if it has a recordingId.
            recording_id = scan_recording_id(latest_user_message.content)
            if recording_id:
                # 3. Analyze recording and, ultimately, enhance prompt.
                state.extra_data['replay_enhance_prompt_id'] = latest_user_message.id
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
):
    enhance_action_id = state.extra_data.get('replay_enhance_prompt_id')
    if enhance_action_id:
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

        output: ReplayCommandResult = safe_parse_json(observation.content)
        if output and output['result']:
            original_prompt = user_message.content
            result: AnnotateResult = output['result']
            annotated_repo = result['annotatedRepo']
            comment_text = result['commentText'] or ''
            point_location = result['pointLocation'] or ''

            # Enhance user prompt with analysis results:
            user_message.content = f'{original_prompt}\n\n<ANALYSYS_RESULTS>\n* The user provided a recording of the bug which was used to clone and annotated the code in "{annotated_repo}".\n* The user reported that the bug occurs at "{point_location}". At that location, the user commented: <USER_COMMENT>{comment_text}</USER_COMMENT>. Start your investigation here! You will see comments pointing to other `reproduction step`s in the code. Search for those steps when you see them mentioned.\n</ANALYSYS_RESULTS>'
