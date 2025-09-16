import hashlib

from evaluation.integration_tests.tests.base import BaseIntegrationTest, TestResult
from openhands.events.action import (
    AgentFinishAction,
    FileWriteAction,
    MessageAction,
)
from openhands.events.event import Event
from openhands.events.observation import AgentDelegateObservation
from openhands.runtime.base import Runtime


class Test(BaseIntegrationTest):
    INSTRUCTION = 'Execute the python script /workspace/python_script.py with input "John" and "25" and tell me the secret number.'
    SECRET_NUMBER = int(hashlib.sha256(str(25).encode()).hexdigest()[:8], 16) % 1000

    @classmethod
    def initialize_runtime(cls, runtime: Runtime) -> None:
        from openhands.core.logger import openhands_logger as logger

        action = FileWriteAction(
            path='/workspace/python_script.py',
            content=(
                'name = input("Enter your name: "); age = input("Enter your age: "); '
                'import hashlib; secret = int(hashlib.sha256(str(age).encode()).hexdigest()[:8], 16) % 1000; '
                'print(f"Hello {name}, you are {age} years old. Tell you a secret number: {secret}")'
            ),
        )
        logger.info(action, extra={'msg_type': 'ACTION'})
        observation = runtime.run_action(action)
        logger.info(observation, extra={'msg_type': 'OBSERVATION'})

    @classmethod
    def verify_result(cls, runtime: Runtime, histories: list[Event]) -> TestResult:
        from openhands.core.logger import openhands_logger as logger

        # check if the license information is in any message
        message_actions = [
            event
            for event in histories
            if isinstance(
                event, (MessageAction, AgentFinishAction, AgentDelegateObservation)
            )
        ]
        logger.info(f'Total message-like events: {len(message_actions)}')

        for event in message_actions:
            try:
                if isinstance(event, AgentDelegateObservation):
                    content = event.content
                elif isinstance(event, AgentFinishAction):
                    content = event.outputs.get('content', '')
                    if event.thought:
                        content += f'\n\n{event.thought}'
                elif isinstance(event, MessageAction):
                    content = event.content
                else:
                    logger.warning(f'Unexpected event type: {type(event)}')
                    continue

                if str(cls.SECRET_NUMBER) in content:
                    return TestResult(success=True)
            except Exception as e:
                logger.error(f'Error processing event: {e}')

        logger.debug(
            f'Total messages: {len(message_actions)}. Messages: {message_actions}'
        )
        return TestResult(
            success=False,
            reason=f'The answer is not found in any message. Total messages: {len(message_actions)}.',
        )
