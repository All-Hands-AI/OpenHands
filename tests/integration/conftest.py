import re
import os
from functools import partial

import pytest
from litellm import completion

script_dir = os.path.dirname(os.path.realpath(__file__))


def filter_out_symbols(input):
    return ' '.join([char for char in input if char.isalpha()])


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
    monkeypatch.setattr('opendevin.llm.llm.litellm_completion', partial(mock_completion, test_name=test_name))
