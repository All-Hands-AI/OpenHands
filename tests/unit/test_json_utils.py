from datetime import datetime

import pytest
from litellm.types.utils import ModelResponse

from openhands.core.exceptions import LLMResponseError
from openhands.core.utils.json import dumps, loads
from openhands.events.event import Event
from openhands.llm.metrics import Metrics


class TestEvent(Event):
    def __init__(self, value):
        super().__init__()
        self.value = value
        self.observation = 'test'  # Makes it an observation event


def test_dumps_datetime():
    dt = datetime(2024, 1, 1, 12, 0, 0)
    result = dumps({'date': dt})
    assert '"2024-01-01T12:00:00"' in result


def test_dumps_event():
    event = TestEvent('test')
    result = dumps({'event': event})
    assert '"observation": "test"' in result


def test_dumps_metrics():
    metrics = Metrics()
    metrics.add_cost(1.0)
    result = dumps({'metrics': metrics})
    assert '"accumulated_cost": 1.0' in result


def test_dumps_model_response():
    response = ModelResponse(
        id='test',
        choices=[{'text': 'test'}],
        model='test-model',
        usage={'total_tokens': 10},
    )
    result = dumps({'response': response})
    assert '"id": "test"' in result
    assert '"model": "test-model"' in result


def test_loads_valid_json():
    json_str = '{"key": "value"}'
    result = loads(json_str)
    assert result == {'key': 'value'}


def test_loads_invalid_json():
    json_str = 'invalid json'
    with pytest.raises(LLMResponseError):
        loads(json_str)


def test_loads_partial_json():
    json_str = 'some text {"key": "value"} more text'
    result = loads(json_str)
    assert result == {'key': 'value'}


def test_loads_invalid_partial_json():
    json_str = 'some text {"key": "value", "invalid": } more text'
    with pytest.raises(LLMResponseError):
        loads(json_str)


def test_loads_no_json():
    json_str = 'no json here'
    with pytest.raises(LLMResponseError):
        loads(json_str)
