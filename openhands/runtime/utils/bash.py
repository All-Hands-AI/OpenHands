import os
import re
from functools import wraps
from typing import Any, Callable, TypeVar, Tuple

import bashlex
import pexpect

from openhands.core.logger import openhands_logger as logger
from openhands.events.action import CmdRunAction
from openhands.events.event import EventSource
from openhands.events.observation import (
    CmdOutputObservation,
    FatalErrorObservation,
)

T = TypeVar('T')

def bash_operation(operation_name: str) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator for bash operations that handles common error patterns"""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            try:
                return func(*args, **kwargs)
            except bashlex.errors.ParsingError as e:
                logger.debug(
                    f'Failed to parse bash commands during {operation_name}\n'
                    f'[warning]: {e}\n'
                    f'The original command will be returned as is.'
                )
                if operation_name == "split_commands":
                    return [args[0]]  # Return original command
            except pexpect.TIMEOUT as e:
                logger.warning(f'Bash pexpect.TIMEOUT during {operation_name}: {e}')
                if operation_name == "execute":
                    return args[0].shell.before or '', -1
            except Exception as e:
                logger.error(f'Error during {operation_name}: {e}')
                if operation_name == "parse_exit_code":
                    return 2
            return None
        return wrapper
    return decorator


@bash_operation("split_commands")
def split_bash_commands(commands: str) -> list[str]:
    if not commands.strip():
        return ['']
    parsed = bashlex.parse(commands)

    result: list[str] = []
    last_end = 0

    for node in parsed:
        start, end = node.pos

        if start > last_end:
            between = commands[last_end:start]
            logger.debug(f'BASH PARSING between: {between}')
            if result:
                result[-1] += between.rstrip()
            elif between.strip():
                result.append(between.rstrip())

        command = commands[start:end].rstrip()
        logger.debug(f'BASH PARSING command: {command}')
        result.append(command)

        last_end = end

    remaining = commands[last_end:].rstrip()
    logger.debug(f'BASH PARSING remaining: {remaining}')
    if last_end < len(commands) and result:
        result[-1] += remaining
        logger.debug(f'BASH PARSING result[-1] += remaining: {result[-1]}')
    elif last_end < len(commands) and remaining:
        result.append(remaining)
        logger.debug(f'BASH PARSING result.append(remaining): {result[-1]}')
    return result


class BashSession:
    """A class that maintains a pexpect process and provides a simple interface for running commands."""

    def __init__(self, work_dir: str, username: str):
        self._pwd = work_dir
        self.shell = pexpect.spawn(
            f'su {username}',
            encoding='utf-8',
            codec_errors='replace',
            echo=False,
        )
        self._init_bash_shell(work_dir)

    def close(self):
        self.shell.close()

    @property
    def pwd(self):
        return self._pwd

    @property
    def workdir(self):
        return self._get_working_directory()

    @bash_operation("get_working_directory")
    def _get_working_directory(self) -> str:
        result, exit_code = self._execute_bash('pwd', timeout=60, keep_prompt=False)
        if exit_code != 0:
            raise RuntimeError(
                f'Failed to get working directory (exit code: {exit_code}): {result}'
            )
        return result.strip()

    def _init_bash_shell(self, work_dir: str):
        self.__bash_PS1 = (
            r'[PEXPECT_BEGIN]\n'
            r'$(which python >/dev/null 2>&1 && echo "[Python Interpreter: $(which python)]\n")'
            r'\u@\h:\w\n'
            r'[PEXPECT_END]'
        )

        self.__bash_expect_regex = r'\[PEXPECT_BEGIN\]\s*(.*?)\s*([a-z0-9_-]*)@([a-zA-Z0-9.-]*):(.+)\s*\[PEXPECT_END\]'
        self.shell.sendline(f'umask 002; export PS1="{self.__bash_PS1}"; export PS2=""')
        self.shell.expect(self.__bash_expect_regex)

        self.shell.sendline(
            f'if [ ! -d "{work_dir}" ]; then mkdir -p "{work_dir}"; fi && cd "{work_dir}"'
        )
        self.shell.expect(self.__bash_expect_regex)
        logger.debug(
            f'Bash initialized. Working directory: {work_dir}. Output: [{self.shell.before}]'
        )
        self.shell.sendline(f'chmod g+rw "{work_dir}"')
        self.shell.expect(self.__bash_expect_regex)

    @bash_operation("get_prompt")
    def _get_bash_prompt_and_update_pwd(self) -> str:
        ps1 = self.shell.after
        if ps1 == pexpect.EOF:
            logger.error(f'Bash shell EOF! {self.shell.after=}, {self.shell.before=}')
            raise RuntimeError('Bash shell EOF')
        if ps1 == pexpect.TIMEOUT:
            logger.warning('Bash shell timeout')
            return ''

        _begin_pos = ps1.rfind('[PEXPECT_BEGIN]')
        if _begin_pos != -1:
            ps1 = ps1[_begin_pos:]

        matched = re.match(self.__bash_expect_regex, ps1)
        assert (
            matched is not None
        ), f'Failed to parse bash prompt: {ps1}. This should not happen.'
        other_info, username, hostname, working_dir = matched.groups()
        working_dir = working_dir.rstrip()
        self._pwd = os.path.expanduser(working_dir)

        prompt = f'{other_info.strip()}\n{username}@openhands-workspace:{working_dir} '
        if username == 'root':
            prompt += '#'
        else:
            prompt += '$'
        return prompt + ' '

    @bash_operation("execute")
    def _execute_bash(
        self,
        command: str,
        timeout: int,
        keep_prompt: bool = True,
        kill_on_timeout: bool = True,
    ) -> tuple[str, int]:
        logger.debug(f'Executing command: {command}')
        self.shell.sendline(command)
        return self._continue_bash(
            timeout=timeout, keep_prompt=keep_prompt, kill_on_timeout=kill_on_timeout
        )

    @bash_operation("interrupt")
    def _interrupt_bash(
        self,
        action_timeout: int | None,
        interrupt_timeout: int | None = None,
        max_retries: int = 2,
    ) -> tuple[str, int]:
        interrupt_timeout = interrupt_timeout or 1
        while max_retries > 0:
            self.shell.sendintr()
            logger.debug('Sent SIGINT to bash. Waiting for output...')
            try:
                self.shell.expect(self.__bash_expect_regex, timeout=interrupt_timeout)
                output = self.shell.before
                logger.debug(f'Received output after SIGINT: {output}')
                exit_code = 130

                _additional_msg = ''
                if action_timeout is not None:
                    _additional_msg = f'Command timed out after {action_timeout} seconds. '
                output += (
                    '\r\n\r\n'
                    + f'[{_additional_msg}SIGINT was sent to interrupt the command.]'
                )
                return output, exit_code
            except pexpect.TIMEOUT as e:
                logger.warning(f'Bash pexpect.TIMEOUT while waiting for SIGINT: {e}')
                max_retries -= 1

        logger.error(
            'Failed to get output after SIGINT. Max retries reached. Sending control-z...'
        )
        self.shell.sendcontrol('z')
        self.shell.expect(self.__bash_expect_regex)
        output = self.shell.before
        logger.debug(f'Received output after control-z: {output}')
        self.shell.sendline('kill -9 %1')
        self.shell.expect(self.__bash_expect_regex)
        logger.debug(f'Received output after killing job %1: {self.shell.before}')
        output += self.shell.before

        _additional_msg = ''
        if action_timeout is not None:
            _additional_msg = f'Command timed out after {action_timeout} seconds. '
        output += (
            '\r\n\r\n'
            + f'[{_additional_msg}SIGINT was sent to interrupt the command, but failed. The command was killed.]'
        )

        self.shell.sendline('echo $?')
        self.shell.expect(self.__bash_expect_regex)
        _exit_code_output = self.shell.before
        exit_code = self._parse_exit_code(_exit_code_output)

        return output, exit_code

    @bash_operation("parse_exit_code")
    def _parse_exit_code(self, output: str) -> int:
        exit_code = int(output.strip().split()[0])
        return exit_code

    @bash_operation("continue")
    def _continue_bash(
        self,
        timeout: int,
        keep_prompt: bool = True,
        kill_on_timeout: bool = True,
    ) -> tuple[str, int]:
        logger.debug(f'Continuing bash with timeout={timeout}')
        try:
            self.shell.expect(self.__bash_expect_regex, timeout=timeout)
            output = self.shell.before

            self.shell.sendline('echo $?')
            logger.debug('Requesting exit code...')
            self.shell.expect(self.__bash_expect_regex, timeout=timeout)
            _exit_code_output = self.shell.before
            exit_code = self._parse_exit_code(_exit_code_output)
        except pexpect.TIMEOUT as e:
            logger.warning(f'Bash pexpect.TIMEOUT while executing bash command: {e}')
            if kill_on_timeout:
                output, exit_code = self._interrupt_bash(action_timeout=timeout)
            else:
                output = self.shell.before or ''
                exit_code = -1
        finally:
            bash_prompt = self._get_bash_prompt_and_update_pwd()
            if keep_prompt:
                output += '\r\n' + bash_prompt
        return output, exit_code

    @bash_operation("run")
    def run(self, action: CmdRunAction) -> CmdOutputObservation | FatalErrorObservation:
        assert (
            action.timeout is not None
        ), f'Timeout argument is required for CmdRunAction: {action}'
        commands = split_bash_commands(action.command)
        all_output = ''
        python_interpreter = ''
        for command in commands:
            if command == '':
                output, exit_code = self._continue_bash(
                    timeout=SOFT_TIMEOUT_SECONDS,
                    keep_prompt=action.keep_prompt,
                    kill_on_timeout=False,
                )
            elif command.lower() == 'ctrl+c':
                output, exit_code = self._interrupt_bash(
                    action_timeout=None,
                )
            else:
                output, exit_code = self._execute_bash(
                    command,
                    timeout=SOFT_TIMEOUT_SECONDS if not action.blocking else action.timeout,
                    keep_prompt=action.keep_prompt,
                )

            if output:
                # Extract Python interpreter path if present
                if '[Python Interpreter:' in output:
                    python_interpreter = re.search(
                        r'\[Python Interpreter: (.*?)\]', output
                    ).group(1)

                all_output += output

            if exit_code != 0 and not action.ignore_errors:
                return FatalErrorObservation(
                    content=f'Command failed with exit code {exit_code}:\n{all_output}',
                    source=EventSource.AGENT,
                )

        return CmdOutputObservation(
            content=all_output,
            source=EventSource.AGENT,
            python_interpreter=python_interpreter,
        )

