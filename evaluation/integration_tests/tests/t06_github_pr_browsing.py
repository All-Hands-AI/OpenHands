from evaluation.integration_tests.tests.base import BaseIntegrationTest, TestResult
from openhands.events.action import AgentFinishAction, MessageAction
from openhands.events.event import Event
from openhands.events.observation import AgentDelegateObservation
from openhands.runtime.base import Runtime


class Test(BaseIntegrationTest):
    INSTRUCTION = 'Look at https://github.com/All-Hands-AI/OpenHands/pull/8, and tell me what is happening there and what did @asadm suggest.'

    @classmethod
    def initialize_runtime(cls, runtime: Runtime) -> None:
        pass

    @classmethod
    def verify_result(cls, runtime: Runtime, histories: list[Event]) -> TestResult:
        # check if the "The answer is OpenHands is all you need!" is in any message
        message_actions = [
            event
            for event in histories
            if isinstance(
                event, (MessageAction, AgentFinishAction, AgentDelegateObservation)
            )
        ]
        for event in message_actions:
            if isinstance(event, AgentDelegateObservation):
                content = event.content
            elif isinstance(event, AgentFinishAction):
                content = event.outputs.get('content', '')
            elif isinstance(event, MessageAction):
                content = event.content
            else:
                raise ValueError(f'Unknown event type: {type(event)}')

            if (
                'non-commercial' in content
                or 'MIT' in content
                or 'Apache 2.0' in content
            ):
                return TestResult(success=True)
        return TestResult(
            success=False,
            reason=f'The answer is not found in any message. Total messages: {len(message_actions)}. Messages: {message_actions}',
        )
