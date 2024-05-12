import io
import os
import re
from functools import partial

import pytest
from litellm import completion

script_dir = os.path.dirname(os.path.realpath(__file__))
workspace_path = os.getenv('WORKSPACE_BASE')


def filter_out_symbols(input):
    return ' '.join([char for char in input if char.isalnum()])


def get_log_id(prompt_log_name):
    match = re.search(r'prompt_(\d+).log', prompt_log_name)
    if match:
        return match.group(1)


def get_mock_response(test_name, messages):
    """
    Find mock response based on prompt. Prompts are stored under nested
    folders under mock folder. If prompt_{id}.log matches,
    then the mock response we're looking for is at response_{id}.log.

    Note: we filter out all non alpha-numerical characters, otherwise we would
    see surprising mismatches caused by linters and minor discrepancies between
    different platforms.

    We could have done a slightly more efficient string match with the same time
    complexity (early-out upon first character mismatch), but it is unnecessary
    for tests. Empirically, different prompts of the same task usually only
    differ near the end of file, so the comparison would be more efficient if
    we start from the end of the file, but again, that is unnecessary and only
    makes test code harder to understand.
    """
    mock_dir = os.path.join(script_dir, 'mock', os.environ.get('AGENT'), test_name)
    prompt = filter_out_symbols(messages)
    for root, _, files in os.walk(mock_dir):
        for file in files:
            if file.startswith('prompt_') and file.endswith('.log'):
                file_path = os.path.join(root, file)
                # Open the prompt file and compare its contents
                with open(file_path, 'r') as f:
                    file_content = filter_out_symbols(f.read())
                    if file_content == prompt:
                        # If a match is found, construct the corresponding response file path
                        log_id = get_log_id(file_path)
                        resp_file_path = os.path.join(root, f'response_{log_id}.log')
                        # Read the response file and return its content
                        with open(resp_file_path, 'r') as resp_file:
                            return resp_file.read()


def mock_user_response(*args, test_name, **kwargs):
    """The agent will ask for user input using `input()` when calling `asyncio.run(main(task))`.
    This function mocks the user input by providing the response from the mock response file.

    It will read the `user_responses.log` file in the test directory and set as
    STDIN input for the agent to read.
    """
    user_response_file = os.path.join(
        script_dir, 'mock', os.environ.get('AGENT'), test_name, 'user_responses.log'
    )
    if not os.path.exists(user_response_file):
        return ''
    with open(user_response_file, 'r') as f:
        ret = f.read().rstrip()
    ret += '\n'
    return ret


def mock_completion(*args, test_name, **kwargs):
    messages = kwargs['messages']
    message_str = ''
    for message in messages:
        message_str += message['content']
    mock_response = get_mock_response(test_name, message_str)
    assert mock_response is not None, 'Mock response for prompt is not found'
    response = completion(**kwargs, mock_response=mock_response)
    return response


@pytest.fixture(autouse=True)
def patch_completion(monkeypatch, request):
    test_name = request.node.name
    # Mock LLM completion
    monkeypatch.setattr(
        'opendevin.llm.llm.litellm_completion',
        partial(mock_completion, test_name=test_name),
    )

    # Mock user input (only for tests that have user_responses.log)
    user_responses_str = mock_user_response(test_name=test_name)
    if user_responses_str:
        user_responses = io.StringIO(user_responses_str)
        monkeypatch.setattr('sys.stdin', user_responses)


def set_up():
    assert workspace_path is not None
    if os.path.exists(workspace_path):
        for file in os.listdir(workspace_path):
            os.remove(os.path.join(workspace_path, file))


@pytest.fixture(autouse=True)
def resource_setup():
    set_up()
    if not os.path.exists(workspace_path):
        os.makedirs(workspace_path)
    # Yield to test execution
    yield
