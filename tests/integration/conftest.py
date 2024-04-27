import os
from functools import partial

import pytest
from litellm import completion

script_dir = os.path.dirname(os.path.realpath(__file__))

cur_id = 1
def mock_completion(*args, test_name, **kwargs):
    global cur_id
    messages = kwargs['messages']
    mock_dir = os.path.join(script_dir, 'mock', os.environ.get('AGENT'), test_name)
    resp_file_path = os.path.join(mock_dir, f'response_{"{0:03}".format(cur_id)}.log')
    cur_id += 1
    try:
        with open(resp_file_path, 'r') as resp_file:
            mock_response = resp_file.read()
    except FileNotFoundError:
        assert False, f'Response file {resp_file_path} not found'
    assert mock_response is not None, f'Mock response for {test_name} not found'
    response = completion(**kwargs, mock_response=mock_response)
    return response


@pytest.fixture(autouse=True)
def patch_completion(monkeypatch, request):
    test_name = request.node.name
    monkeypatch.setattr('opendevin.llm.llm.litellm_completion', partial(mock_completion, test_name=test_name))
