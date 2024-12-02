import tempfile
from os import chmod, unlink

from openhands.events.action.commands import CmdRunAction
from openhands.events.action.replay import ReplayCmdRunAction
from openhands.events.observation.error import ErrorObservation
from openhands.events.observation.replay import ReplayCmdOutputObservation
from openhands.runtime.utils.bash import BashSession


class ReplayCli:
    def __init__(self, bash_session: BashSession):
        self.bash_session = bash_session

    async def run_action(
        self, action: ReplayCmdRunAction
    ) -> ReplayCmdOutputObservation | ErrorObservation:
        command = f'/replay/replayapi/scripts/run.sh {action.command}'
        if action.recording_id != '':
            command = command + f' -r {action.recording_id}'
        if action.session_id != '':
            command = command + f' -s {action.session_id}'
        tmp_files: list[str] = []
        if action.file_arguments:
            # Write file arguments to temporary files and append to command.
            for arg in action.file_arguments:
                with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
                    tmp_files.append(tmp.name)
                    tmp.write(arg)
                    file_path = tmp.name
                    chmod(file_path, 0o644)  # Make sure bash_session can read the file.
                    command = command + f' {file_path}'
        if action.in_workspace_dir:
            # Execute command from workspace directory.
            command = f'pushd {self.bash_session.workdir} > /dev/null; {command}; popd > /dev/null'

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

        for fpath in tmp_files:
            # Delete tmp file.
            unlink(fpath)

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
