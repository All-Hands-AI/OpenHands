from unittest.mock import Mock, patch

import pytest

from opendevin.core.exceptions import LLMResponseError
from opendevin.llm.llm import LLM
from opendevin.memory.condenser import MemoryCondenser


@pytest.fixture
def memory_condenser():
    return MemoryCondenser()


@pytest.fixture
def mock_llm():
    return Mock(spec=LLM)


def test_condense_success(memory_condenser, mock_llm):
    mock_llm.completion.return_value = {
        'choices': [{'message': {'content': 'Condensed memory'}}]
    }
    result = memory_condenser.condense('Summarize this', mock_llm)
    assert result == 'Condensed memory'
    mock_llm.completion.assert_called_once_with(
        messages=[{'content': 'Summarize this', 'role': 'user'}]
    )


def test_condense_exception(memory_condenser, mock_llm):
    mock_llm.completion.side_effect = LLMResponseError('LLM error')
    with pytest.raises(LLMResponseError, match='LLM error'):
        memory_condenser.condense('Summarize this', mock_llm)


@patch('opendevin.memory.condenser.logger')
def test_condense_logs_error(mock_logger, memory_condenser, mock_llm):
    mock_llm.completion.side_effect = LLMResponseError('LLM error')
    with pytest.raises(LLMResponseError):
        memory_condenser.condense('Summarize this', mock_llm)
    mock_logger.error.assert_called_once_with(
        'Error condensing thoughts: %s', 'LLM error', exc_info=False
    )
