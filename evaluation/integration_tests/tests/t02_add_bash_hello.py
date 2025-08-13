from evaluation.integration_tests.tests.base import BaseIntegrationTest, TestResult
from evaluation.utils.shared import assert_and_raise
from openhands.events.action import CmdRunAction
from openhands.events.event import Event
from openhands.runtime.base import Runtime


class Test(BaseIntegrationTest):
    INSTRUCTION = "Write a shell script '/workspace/hello.sh' that prints 'hello'."

    @classmethod
    def initialize_runtime(cls, runtime: Runtime) -> None:
        action = CmdRunAction(command='mkdir -p /workspace')
        obs = runtime.run_action(action)
        assert_and_raise(obs.exit_code == 0, f'Failed to run command: {obs.content}')

    @classmethod
    def verify_result(cls, runtime: Runtime, histories: list[Event]) -> TestResult:
        # check if the file /workspace/hello.sh exists
        action = CmdRunAction(command='cat /workspace/hello.sh')
        obs = runtime.run_action(action)
        if obs.exit_code != 0:
            return TestResult(
                success=False,
                reason=f'Failed to cat /workspace/hello.sh: {obs.content}.',
            )

        # execute the script
        action = CmdRunAction(command='bash /workspace/hello.sh')
        obs = runtime.run_action(action)
        if obs.exit_code != 0:
            return TestResult(
                success=False,
                reason=f'Failed to execute /workspace/hello.sh: {obs.content}.',
            )
        if obs.content.strip() != 'hello':
            return TestResult(
                success=False, reason=f'Script did not print "hello": {obs.content}.'
            )
        return TestResult(success=True)
