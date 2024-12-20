import os
import tempfile

from evaluation.integration_tests.tests.base import BaseIntegrationTest, TestResult
from openhands.events.action import CmdRunAction
from openhands.events.event import Event
from openhands.runtime.base import Runtime


class Test(BaseIntegrationTest):
    INSTRUCTION = 'Fix typos in bad.txt.'

    @classmethod
    def initialize_runtime(cls, runtime: Runtime) -> None:
        # create a file with a typo in /workspace/bad.txt
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file_path = os.path.join(temp_dir, 'bad.txt')
            with open(temp_file_path, 'w') as f:
                f.write('This is a stupid typoo.\nReally?\nNo mor typos!\nEnjoy!')

            # Copy the file to the desired location
            runtime.copy_to(temp_file_path, '/workspace')

    @classmethod
    def verify_result(cls, runtime: Runtime, histories: list[Event]) -> TestResult:
        # check if the file /workspace/bad.txt has been fixed
        action = CmdRunAction(command='cat /workspace/bad.txt')
        obs = runtime.run_action(action)
        if obs.exit_code != 0:
            return TestResult(
                success=False, reason=f'Failed to run command: {obs.content}'
            )
        # check if the file /workspace/bad.txt has been fixed
        if (
            obs.content.strip().replace('\r\n', '\n')
            == 'This is a stupid typo.\nReally?\nNo more typos!\nEnjoy!'
        ):
            return TestResult(success=True)
        return TestResult(success=False, reason=f'File not fixed: {obs.content}')
