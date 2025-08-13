from evaluation.integration_tests.tests.base import BaseIntegrationTest, TestResult
from evaluation.utils.shared import assert_and_raise
from openhands.events.action import CmdRunAction
from openhands.events.event import Event
from openhands.runtime.base import Runtime


class Test(BaseIntegrationTest):
    INSTRUCTION = "Use Jupyter IPython to write a text file containing 'hello world' to '/workspace/test.txt'."

    @classmethod
    def initialize_runtime(cls, runtime: Runtime) -> None:
        action = CmdRunAction(command='mkdir -p /workspace')
        obs = runtime.run_action(action)
        assert_and_raise(obs.exit_code == 0, f'Failed to run command: {obs.content}')

    @classmethod
    def verify_result(cls, runtime: Runtime, histories: list[Event]) -> TestResult:
        # check if the file /workspace/hello.sh exists
        action = CmdRunAction(command='cat /workspace/test.txt')
        obs = runtime.run_action(action)
        if obs.exit_code != 0:
            return TestResult(
                success=False,
                reason=f'Failed to cat /workspace/test.txt: {obs.content}.',
            )

        # execute the script
        action = CmdRunAction(command='cat /workspace/test.txt')
        obs = runtime.run_action(action)

        if obs.exit_code != 0:
            return TestResult(
                success=False,
                reason=f'Failed to cat /workspace/test.txt: {obs.content}.',
            )

        if 'hello world' not in obs.content.strip():
            return TestResult(
                success=False,
                reason=f'File did not contain "hello world": {obs.content}.',
            )
        return TestResult(success=True)
