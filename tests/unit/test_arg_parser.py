import pytest

from opendevin.core.config import get_parser


def test_help_message(capsys):
    parser = get_parser()
    with pytest.raises(SystemExit):  # `--help` causes SystemExit
        parser.parse_args(['--help'])
    captured = capsys.readouterr()
    expected_help_message = """
usage: pytest [-h] [-d DIRECTORY] [-t TASK] [-f FILE] [-c AGENT_CLS]
[-m MODEL_NAME] [-i MAX_ITERATIONS] [-n MAX_CHARS]

Run an agent with a specific task

options:
  -h, --help            show this help message and exit
  -d DIRECTORY, --directory DIRECTORY
                        The working directory for the agent
  -t TASK, --task TASK  The task for the agent to perform
  -f FILE, --file FILE  Path to a file containing the task. Overrides -t if
  both are provided.
  -c AGENT_CLS, --agent-cls AGENT_CLS
                        The agent class to use
  -m MODEL_NAME, --model-name MODEL_NAME
                        The (litellm) model name to use
  -i MAX_ITERATIONS, --max-iterations MAX_ITERATIONS
                        The maximum number of iterations to run the agent
  -n MAX_CHARS, --max-chars MAX_CHARS
                        The maximum number of characters to send to and
                        receive from LLM per task
"""
    actual_lines = captured.out.strip().split('\n')
    expected_lines = expected_help_message.strip().split('\n')

    # Ensure both outputs have the same number of lines
    assert len(actual_lines) == len(
        expected_lines
    ), 'The number of lines in the help message does not match.'

    # Compare each line
    for actual, expected in zip(actual_lines, expected_lines):
        assert (
            actual.strip() == expected.strip()
        ), f"Expected '{expected}', got '{actual}'"
