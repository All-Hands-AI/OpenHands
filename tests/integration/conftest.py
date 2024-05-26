import io
import os
import re
import sys
from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler
from threading import Thread

import pytest
from litellm import completion

from opendevin.llm.llm import message_separator

script_dir = os.path.dirname(os.path.realpath(__file__))
workspace_path = os.getenv('WORKSPACE_BASE')


def filter_out_symbols(input):
    return ' '.join([char for char in input if char.isalnum()])


def get_log_id(prompt_log_name):
    match = re.search(r'prompt_(\d+).log', prompt_log_name)
    if match:
        return match.group(1)


def apply_prompt_and_get_mock_response(test_name: str, messages: str, id: int) -> str:
    """
    Apply the mock prompt, and find mock response based on id.
    If there is no matching response file, return None.

    Note: this function blindly replaces existing prompt file with the given
    input without checking the contents.
    """
    mock_dir = os.path.join(script_dir, 'mock', os.environ.get('AGENT'), test_name)
    prompt_file_path = os.path.join(mock_dir, f'prompt_{"{0:03}".format(id)}.log')
    resp_file_path = os.path.join(mock_dir, f'response_{"{0:03}".format(id)}.log')
    try:
        # load response
        with open(resp_file_path, 'r') as resp_file:
            response = resp_file.read()
        # apply prompt
        with open(prompt_file_path, 'w') as prompt_file:
            prompt_file.write(messages)
        return response
    except FileNotFoundError:
        return None


def get_mock_response(test_name: str, messages: str, id: int) -> str:
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
    mock_dir = os.path.join(script_dir, 'mock', os.environ.get('AGENT'), test_name)
    prompt_file_path = os.path.join(mock_dir, f'prompt_{"{0:03}".format(id)}.log')
    resp_file_path = os.path.join(mock_dir, f'response_{"{0:03}".format(id)}.log')
    # Open the prompt file and compare its contents
    with open(prompt_file_path, 'r') as f:
        file_content = filter_out_symbols(f.read())
        if file_content == prompt:
            # Read the response file and return its content
            with open(resp_file_path, 'r') as resp_file:
                return resp_file.read()
        else:
            # print the mismatched lines
            print('Mismatched Prompt File path', prompt_file_path)
            print('---' * 10)
            print(messages)
            print('---' * 10)
            for i, (c1, c2) in enumerate(zip(file_content, prompt)):
                if c1 != c2:
                    print(
                        f'Mismatch at index {i}: {c1[max(0,i-100):i+100]} vs {c2[max(0,i-100):i+100]}'
                    )
                    break


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
    global cur_id
    messages = kwargs['messages']
    message_str = ''
    for message in messages:
        message_str += message_separator + message['content']
    # this assumes all response_(*).log filenames are in numerical order, starting from one
    cur_id += 1
    if os.environ.get('FORCE_APPLY_PROMPTS') == 'true':
        mock_response = apply_prompt_and_get_mock_response(
            test_name, message_str, cur_id
        )
    else:
        mock_response = get_mock_response(test_name, message_str, cur_id)
    if mock_response is None:
        print('Mock response for prompt is not found\n\n')
        print('Exiting...')
        sys.exit(1)
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


@pytest.fixture
def http_server():
    web_dir = os.path.join(os.path.dirname(__file__), 'static')
    os.chdir(web_dir)
    handler = SimpleHTTPRequestHandler

    # Start the server
    server = HTTPServer(('localhost', 8000), handler)
    thread = Thread(target=server.serve_forever)
    thread.setDaemon(True)
    thread.start()

    yield server

    # Stop the server
    server.shutdown()
    thread.join()


def set_up():
    global cur_id
    cur_id = 0
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
