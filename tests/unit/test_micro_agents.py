import json
import os
from unittest.mock import MagicMock

import yaml

from agenthub.micro.registry import all_microagents
from opendevin.controller.agent import Agent
from opendevin.controller.state.state import State
from opendevin.events import EventSource
from opendevin.events.action import MessageAction
from opendevin.events.observation import NullObservation


def test_all_agents_are_loaded():
    full_path = os.path.join('agenthub', 'micro')
    agent_names = set()
    for root, _, files in os.walk(full_path):
        for file in files:
            if file == 'agent.yaml':
                file_path = os.path.join(root, file)
                with open(file_path, 'r') as yaml_file:
                    data = yaml.safe_load(yaml_file)
                    agent_names.add(data['name'])
    assert agent_names == set(all_microagents.keys())


def test_coder_agent_with_summary():
    """
    Coder agent should render code summary as part of prompt
    """
    mock_llm = MagicMock()
    content = json.dumps({'action': 'finish', 'args': {}})
    mock_llm.do_completion.return_value = {
        'choices': [{'message': {'content': content}}]
    }

    coder_agent = Agent.get_cls('CoderAgent')(llm=mock_llm)
    assert coder_agent is not None

    task = 'This is a dummy task'
    history = [(MessageAction(content=task), NullObservation(''))]
    history[0][0]._source = EventSource.USER
    summary = 'This is a dummy summary about this repo'
    state = State(history=history, inputs={'summary': summary})
    coder_agent.step(state)

    mock_llm.do_completion.assert_called_once()
    _, kwargs = mock_llm.do_completion.call_args
    prompt = kwargs['messages'][0]['content']
    assert task in prompt
    assert "Here's a summary of the codebase, as it relates to this task" in prompt
    assert summary in prompt


def test_coder_agent_without_summary():
    """
    When there's no codebase_summary available, there shouldn't be any prompt
    about 'code summary'
    """
    mock_llm = MagicMock()
    content = json.dumps({'action': 'finish', 'args': {}})
    mock_llm.do_completion.return_value = {
        'choices': [{'message': {'content': content}}]
    }

    coder_agent = Agent.get_cls('CoderAgent')(llm=mock_llm)
    assert coder_agent is not None

    task = 'This is a dummy task'
    history = [(MessageAction(content=task), NullObservation(''))]
    history[0][0]._source = EventSource.USER
    state = State(history=history)
    coder_agent.step(state)

    mock_llm.do_completion.assert_called_once()
    _, kwargs = mock_llm.do_completion.call_args
    prompt = kwargs['messages'][0]['content']
    assert task in prompt
    assert "Here's a summary of the codebase, as it relates to this task" not in prompt
