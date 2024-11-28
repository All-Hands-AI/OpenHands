from openhands.events.action.action import ActionConfirmationStatus
from openhands.events.action.commands import CmdRunAction
from openhands.events.action.replay import ReplayCmdRunAction
from openhands.events.observation.error import ErrorObservation
from openhands.events.observation.replay import ReplayCmdOutputObservation
from openhands.runtime.utils.bash import BashSession


class ReplayCli:
    def __init__(self, bash_session: BashSession):
        self.bash_session = bash_session

    def run(self, command: str):
        command = f'/replay/replayapi/scripts/run.sh {command}'

        cmd_action = CmdRunAction(
            command=command,
            blocking=True,
            # Whether to show the output.
            keep_prompt=True,
            # Whether to hide the input.
            hidden=False,
            # (Seemingly) unused parameters
            thought='',
            confirmation_state=ActionConfirmationStatus.CONFIRMED,
            security_risk=None,
        )
        cmd_action.timeout = 600
        obs = self.bash_session.run(cmd_action)

        if isinstance(obs, ErrorObservation):
            return obs

        # we might not actually need a separate observation type for replay...
        return ReplayCmdOutputObservation(
            command_id=obs.command_id,
            command=obs.command,
            exit_code=obs.exit_code,
            hidden=obs.hidden,
            interpreter_details=obs.interpreter_details,
            content=obs.content,
        )

    async def run_action(
        self, action: ReplayCmdRunAction
    ) -> ReplayCmdOutputObservation | ErrorObservation:
        command = f'/replay/replayapi/scripts/run.sh {action.command}'
        if action.recording_id != '':
            command = command + f' -r {action.recording_id}'
        if action.session_id != '':
            command = command + f' -s {action.session_id}'

        cmd_action = CmdRunAction(
            command=command,
            thought=action.thought,
            blocking=action.blocking,
            keep_prompt=action.keep_prompt,
            hidden=action.hidden,
            confirmation_state=action.confirmation_state,
            security_risk=action.security_risk,
        )
        cmd_action.timeout = 600
        obs = self.bash_session.run(cmd_action)

        if isinstance(obs, ErrorObservation):
            return obs

        # we might not actually need a separate observation type for replay...
        return ReplayCmdOutputObservation(
            command_id=obs.command_id,
            command=obs.command,
            exit_code=obs.exit_code,
            hidden=obs.hidden,
            interpreter_details=obs.interpreter_details,
            content=obs.content,
        )
