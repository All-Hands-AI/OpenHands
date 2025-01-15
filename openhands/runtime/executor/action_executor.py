import base64
import json
import mimetypes
import os
from pathlib import Path
import re
from openhands_aci.utils.diff import get_diff
from openhands.core.logger import openhands_logger as logger
from openhands.events.action.browse import BrowseInteractiveAction, BrowseURLAction
from openhands.events.action.commands import IPythonRunCellAction
from openhands.events.action.files import FileReadAction, FileWriteAction
from openhands.events.event import FileEditSource, FileReadSource
from openhands.events.observation.commands import (
    IPythonRunCellObservation,
)
from openhands.events.observation.error import ErrorObservation
from openhands.events.observation.files import (
    FileEditObservation,
    FileReadObservation,
    FileWriteObservation,
)
from openhands.events.observation.observation import Observation
from openhands.runtime.browser import browse
from openhands.runtime.executor.base import RuntimeExecutor
from openhands.runtime.plugins.jupyter import JupyterPlugin
from openhands.runtime.utils.files import insert_lines, read_lines


class BaseActionExecutor(RuntimeExecutor):
    """Runtime executor that dynamically dispatches actions to the appropriate method based on their name."""

    async def run_action(self, action) -> Observation:
        async with self.lock:
            action_type = action.action
            logger.debug(f'Running action:\n{action}')
            observation = await getattr(self, action_type)(action)
            logger.debug(f'Action output:\n{observation}')
            return observation


class ActionExecutor(BaseActionExecutor):
    """ActionExecutor runs inside docker sandbox.
    It is responsible for executing actions received from OpenHands backend and producing observations.
    It is a BaseActionExectuor that provides a default implementation for all of the built-in actions.
    """

    async def run_ipython(self, action: IPythonRunCellAction) -> Observation:
        assert self.bash_session is not None
        if 'jupyter' in self.plugins:
            _jupyter_plugin: JupyterPlugin = self.plugins['jupyter']  # type: ignore
            # This is used to make AgentSkills in Jupyter aware of the
            # current working directory in Bash
            jupyter_cwd = getattr(self, '_jupyter_cwd', None)
            if self.bash_session.cwd != jupyter_cwd:
                logger.debug(
                    f'{self.bash_session.cwd} != {jupyter_cwd} -> reset Jupyter PWD'
                )
                reset_jupyter_cwd_code = (
                    f'import os; os.chdir("{self.bash_session.cwd}")'
                )
                _aux_action = IPythonRunCellAction(code=reset_jupyter_cwd_code)
                _reset_obs: IPythonRunCellObservation = await _jupyter_plugin.run(
                    _aux_action
                )
                logger.debug(
                    f'Changed working directory in IPython to: {self.bash_session.cwd}. Output: {_reset_obs}'
                )
                self._jupyter_cwd = self.bash_session.cwd

            obs: IPythonRunCellObservation = await _jupyter_plugin.run(action)
            obs.content = obs.content.rstrip()
            matches = re.findall(
                r'<oh_aci_output_[0-9a-f]{32}>(.*?)</oh_aci_output_[0-9a-f]{32}>',
                obs.content,
                re.DOTALL,
            )
            if matches:
                results: list[str] = []
                if len(matches) == 1:
                    # Use specific actions/observations types
                    match = matches[0]
                    try:
                        result_dict = json.loads(match)
                        if result_dict.get('path'):  # Successful output
                            if (
                                result_dict['new_content'] is not None
                            ):  # File edit commands
                                diff = get_diff(
                                    old_contents=result_dict['old_content']
                                    or '',  # old_content is None when file is created
                                    new_contents=result_dict['new_content'],
                                    filepath=result_dict['path'],
                                )
                                return FileEditObservation(
                                    content=diff,
                                    path=result_dict['path'],
                                    old_content=result_dict['old_content'],
                                    new_content=result_dict['new_content'],
                                    prev_exist=result_dict['prev_exist'],
                                    impl_source=FileEditSource.OH_ACI,
                                    formatted_output_and_error=result_dict[
                                        'formatted_output_and_error'
                                    ],
                                )
                            else:  # File view commands
                                return FileReadObservation(
                                    content=result_dict['formatted_output_and_error'],
                                    path=result_dict['path'],
                                    impl_source=FileReadSource.OH_ACI,
                                )
                        else:  # Error output
                            results.append(result_dict['formatted_output_and_error'])
                    except json.JSONDecodeError:
                        # Handle JSON decoding errors if necessary
                        results.append(
                            f"Invalid JSON in 'openhands-aci' output: {match}"
                        )
                else:
                    for match in matches:
                        try:
                            result_dict = json.loads(match)
                            results.append(result_dict['formatted_output_and_error'])
                        except json.JSONDecodeError:
                            # Handle JSON decoding errors if necessary
                            results.append(
                                f"Invalid JSON in 'openhands-aci' output: {match}"
                            )

                # Combine the results (e.g., join them) or handle them as required
                obs.content = '\n'.join(str(result) for result in results)

            if action.include_extra:
                obs.content += (
                    f'\n[Jupyter current working directory: {self.bash_session.cwd}]'
                )
                obs.content += f'\n[Jupyter Python interpreter: {_jupyter_plugin.python_interpreter_path}]'
            return obs
        else:
            raise RuntimeError(
                'JupyterRequirement not found. Unable to run IPython action.'
            )

    def _resolve_path(self, path: str, working_dir: str) -> str:
        filepath = Path(path)
        if not filepath.is_absolute():
            return str(Path(working_dir) / filepath)
        return str(filepath)

    async def read(self, action: FileReadAction) -> Observation:
        assert self.bash_session is not None
        if action.impl_source == FileReadSource.OH_ACI:
            return await self.run_ipython(
                IPythonRunCellAction(
                    code=action.translated_ipython_code,
                    include_extra=False,
                )
            )

        # NOTE: the client code is running inside the sandbox,
        # so there's no need to check permission
        working_dir = self.bash_session.cwd
        filepath = self._resolve_path(action.path, working_dir)
        try:
            if filepath.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                with open(filepath, 'rb') as file:
                    image_data = file.read()
                    encoded_image = base64.b64encode(image_data).decode('utf-8')
                    mime_type, _ = mimetypes.guess_type(filepath)
                    if mime_type is None:
                        mime_type = 'image/png'  # default to PNG if mime type cannot be determined
                    encoded_image = f'data:{mime_type};base64,{encoded_image}'

                return FileReadObservation(path=filepath, content=encoded_image)
            elif filepath.lower().endswith('.pdf'):
                with open(filepath, 'rb') as file:
                    pdf_data = file.read()
                    encoded_pdf = base64.b64encode(pdf_data).decode('utf-8')
                    encoded_pdf = f'data:application/pdf;base64,{encoded_pdf}'
                return FileReadObservation(path=filepath, content=encoded_pdf)
            elif filepath.lower().endswith(('.mp4', '.webm', '.ogg')):
                with open(filepath, 'rb') as file:
                    video_data = file.read()
                    encoded_video = base64.b64encode(video_data).decode('utf-8')
                    mime_type, _ = mimetypes.guess_type(filepath)
                    if mime_type is None:
                        mime_type = 'video/mp4'  # default to MP4 if MIME type cannot be determined
                    encoded_video = f'data:{mime_type};base64,{encoded_video}'

                return FileReadObservation(path=filepath, content=encoded_video)

            with open(filepath, 'r', encoding='utf-8') as file:
                lines = read_lines(file.readlines(), action.start, action.end)
        except FileNotFoundError:
            return ErrorObservation(
                f'File not found: {filepath}. Your current working directory is {working_dir}.'
            )
        except UnicodeDecodeError:
            return ErrorObservation(f'File could not be decoded as utf-8: {filepath}.')
        except IsADirectoryError:
            return ErrorObservation(
                f'Path is a directory: {filepath}. You can only read files'
            )

        code_view = ''.join(lines)
        return FileReadObservation(path=filepath, content=code_view)

    async def write(self, action: FileWriteAction) -> Observation:
        assert self.bash_session is not None
        working_dir = self.bash_session.cwd
        filepath = self._resolve_path(action.path, working_dir)

        insert = action.content.split('\n')
        try:
            if not os.path.exists(os.path.dirname(filepath)):
                os.makedirs(os.path.dirname(filepath))

            file_exists = os.path.exists(filepath)
            if file_exists:
                file_stat = os.stat(filepath)
            else:
                file_stat = None

            mode = 'w' if not file_exists else 'r+'
            try:
                with open(filepath, mode, encoding='utf-8') as file:
                    if mode != 'w':
                        all_lines = file.readlines()
                        new_file = insert_lines(
                            insert, all_lines, action.start, action.end
                        )
                    else:
                        new_file = [i + '\n' for i in insert]

                    file.seek(0)
                    file.writelines(new_file)
                    file.truncate()

                # Handle file permissions
                if file_exists:
                    assert file_stat is not None
                    # restore the original file permissions if the file already exists
                    os.chmod(filepath, file_stat.st_mode)
                    os.chown(filepath, file_stat.st_uid, file_stat.st_gid)
                else:
                    # set the new file permissions if the file is new
                    os.chmod(filepath, 0o664)
                    os.chown(filepath, self.user_id, self.user_id)

            except FileNotFoundError:
                return ErrorObservation(f'File not found: {filepath}')
            except IsADirectoryError:
                return ErrorObservation(
                    f'Path is a directory: {filepath}. You can only write to files'
                )
            except UnicodeDecodeError:
                return ErrorObservation(
                    f'File could not be decoded as utf-8: {filepath}'
                )
        except PermissionError:
            return ErrorObservation(f'Malformed paths not permitted: {filepath}')
        return FileWriteObservation(content='', path=filepath)

    async def browse(self, action: BrowseURLAction) -> Observation:
        return await browse(action, self.browser)

    async def browse_interactive(self, action: BrowseInteractiveAction) -> Observation:
        return await browse(action, self.browser)
