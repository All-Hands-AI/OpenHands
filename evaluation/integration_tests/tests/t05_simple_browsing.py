import os
import tempfile

from evaluation.integration_tests.tests.base import BaseIntegrationTest, TestResult
from evaluation.utils.shared import assert_and_raise
from openhands.events.action import AgentFinishAction, CmdRunAction, MessageAction
from openhands.events.event import Event
from openhands.events.observation import AgentDelegateObservation
from openhands.runtime.base import Runtime

HTML_FILE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>The Ultimate Answer</title>
    <style>
        body {
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            background: linear-gradient(to right, #1e3c72, #2a5298);
            color: #fff;
            font-family: 'Arial', sans-serif;
            text-align: center;
        }
        .container {
            text-align: center;
            padding: 20px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.2);
        }
        h1 {
            font-size: 36px;
            margin-bottom: 20px;
        }
        p {
            font-size: 18px;
            margin-bottom: 30px;
        }
        #showButton {
            padding: 10px 20px;
            font-size: 16px;
            color: #1e3c72;
            background: #fff;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            transition: background 0.3s ease;
        }
        #showButton:hover {
            background: #f0f0f0;
        }
        #result {
            margin-top: 20px;
            font-size: 24px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>The Ultimate Answer</h1>
        <p>Click the button to reveal the answer to life, the universe, and everything.</p>
        <button id="showButton">Click me</button>
        <div id="result"></div>
    </div>
    <script>
        document.getElementById('showButton').addEventListener('click', function() {
            document.getElementById('result').innerText = 'The answer is OpenHands is all you need!';
        });
    </script>
</body>
</html>
"""


class Test(BaseIntegrationTest):
    INSTRUCTION = 'Browse localhost:8000, and tell me the ultimate answer to life.'

    @classmethod
    def initialize_runtime(cls, runtime: Runtime) -> None:
        action = CmdRunAction(command='mkdir -p /workspace', keep_prompt=False)
        obs = runtime.run_action(action)
        assert_and_raise(obs.exit_code == 0, f'Failed to run command: {obs.content}')

        action = CmdRunAction(command='mkdir -p /tmp/server', keep_prompt=False)
        obs = runtime.run_action(action)
        assert_and_raise(obs.exit_code == 0, f'Failed to run command: {obs.content}')

        # create a file with a typo in /workspace/bad.txt
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file_path = os.path.join(temp_dir, 'index.html')
            with open(temp_file_path, 'w') as f:
                f.write(HTML_FILE)
            # Copy the file to the desired location
            runtime.copy_to(temp_file_path, '/tmp/server')

        # create README.md
        action = CmdRunAction(
            command='cd /tmp/server && nohup python3 -m http.server 8000 &',
            keep_prompt=False,
        )
        obs = runtime.run_action(action)

    @classmethod
    def verify_result(cls, runtime: Runtime, histories: list[Event]) -> TestResult:
        from openhands.core.logger import openhands_logger as logger

        # check if the "The answer is OpenHands is all you need!" is in any message
        message_actions = [
            event
            for event in histories
            if isinstance(
                event, (MessageAction, AgentFinishAction, AgentDelegateObservation)
            )
        ]
        logger.debug(f'Total message-like events: {len(message_actions)}')

        for event in message_actions:
            try:
                if isinstance(event, AgentDelegateObservation):
                    content = event.content
                elif isinstance(event, AgentFinishAction):
                    content = event.outputs.get('content', '')
                elif isinstance(event, MessageAction):
                    content = event.content
                else:
                    logger.warning(f'Unexpected event type: {type(event)}')
                    continue

                if 'OpenHands is all you need!' in content:
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
