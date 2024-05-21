import logging
from io import StringIO

import pytest

from opendevin.core.logger import opendevin_logger as opendevin_logger


@pytest.fixture
def test_handler():
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(message)s')
    handler.setFormatter(formatter)
    opendevin_logger.addHandler(handler)
    yield opendevin_logger, stream
    opendevin_logger.removeHandler(handler)


def test_openai_api_key_masking(test_handler):
    logger, stream = test_handler

    api_key = 'sk-1234567890abcdef'
    message = f"OpenAI API key: api_key='{api_key}'and there's some stuff here"
    logger.info(message)
    log_output = stream.getvalue()
    assert "api_key='******'" in log_output
    assert api_key not in log_output


def test_azure_api_key_masking(test_handler):
    logger, stream = test_handler
    api_key = '1a2b3c4d5e6f7g8h9i0j'
    message = f"Azure API key: api_key='{api_key}' and chatty chat with ' and \" and '"
    logger.info(message)
    log_output = stream.getvalue()
    assert "api_key='******'" in log_output
    assert api_key not in log_output


def test_google_vertex_api_key_masking(test_handler):
    logger, stream = test_handler
    api_key = 'AIzaSyA1B2C3D4E5F6G7H8I9J0'
    message = f"Google Vertex API key: api_key='{api_key}' or not"
    logger.info(message)
    log_output = stream.getvalue()
    assert "api_key='******'" in log_output
    assert api_key not in log_output


def test_anthropic_api_key_masking(test_handler):
    logger, stream = test_handler
    api_key = 'sk-ant-1234567890abcdef'
    message = f"Anthropic API key: api_key='{api_key}' and there's some 'stuff' here"
    logger.info(message)
    log_output = stream.getvalue()
    assert "api_key='******'" in log_output
    assert api_key not in log_output
