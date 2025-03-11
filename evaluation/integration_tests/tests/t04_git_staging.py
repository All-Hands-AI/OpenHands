from evaluation.integration_tests.tests.base import BaseIntegrationTest, TestResult
from evaluation.utils.shared import assert_and_raise
from openhands.events.action import CmdRunAction
from openhands.events.event import Event
from openhands.runtime.base import Runtime


class Test(BaseIntegrationTest):
    INSTRUCTION = 'Write a git commit message for the current staging area and commit the changes.'

    @classmethod
    def initialize_runtime(cls, runtime: Runtime) -> None:
        action = CmdRunAction(command='mkdir -p /workspace')
        obs = runtime.run_action(action)
        assert_and_raise(obs.exit_code == 0, f'Failed to run command: {obs.content}')

        # git init
        action = CmdRunAction(command='git init')
        obs = runtime.run_action(action)
        assert_and_raise(obs.exit_code == 0, f'Failed to run command: {obs.content}')

        # create README.md
        action = CmdRunAction(command='echo \'print("hello world")\' > hello.py')
        obs = runtime.run_action(action)
        assert_and_raise(obs.exit_code == 0, f'Failed to run command: {obs.content}')

        # git add README.md
        action = CmdRunAction(command='git add hello.py')
        obs = runtime.run_action(action)
        assert_and_raise(obs.exit_code == 0, f'Failed to run command: {obs.content}')

    @classmethod
    def verify_result(cls, runtime: Runtime, histories: list[Event]) -> TestResult:
        # check if the file /workspace/hello.py exists
        action = CmdRunAction(command='cat /workspace/hello.py')
        obs = runtime.run_action(action)
        if obs.exit_code != 0:
            return TestResult(
                success=False,
                reason=f'Failed to cat /workspace/hello.py: {obs.content}.',
            )

        # check if the staging area is empty
        action = CmdRunAction(command='git status')
        obs = runtime.run_action(action)
        if obs.exit_code != 0:
            return TestResult(
                success=False, reason=f'Failed to git status: {obs.content}.'
            )
        if 'nothing to commit, working tree clean' in obs.content.strip():
            return TestResult(success=True)

        return TestResult(
            success=False,
            reason=f'Failed to check for "nothing to commit, working tree clean": {obs.content}.',
        )
