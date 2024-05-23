import logging
from io import StringIO

import pytest

from opendevin.core.config import AppConfig, LLMConfig
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
    api_key = 'sk-ant-1234567890abcdef-some-more-stuff-here'
    message = f"Anthropic API key: api_key='{api_key}' and there's some 'stuff' here"
    logger.info(message)
    log_output = stream.getvalue()
    assert "api_key='******'" in log_output
    assert api_key not in log_output


def test_llm_config_attributes_masking(test_handler):
    logger, stream = test_handler
    llm_config = LLMConfig(
        api_key='sk-abc123',
        aws_access_key_id='AKIAIOSFODNN7EXAMPLE',
        aws_secret_access_key='wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY',
    )
    logger.info(f'LLM Config: {llm_config}')
    log_output = stream.getvalue()
    assert "api_key='******'" in log_output
    assert "aws_access_key_id='******'" in log_output
    assert "aws_secret_access_key='******'" in log_output
    assert 'sk-abc123' not in log_output
    assert 'AKIAIOSFODNN7EXAMPLE' not in log_output
    assert 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY' not in log_output

    # reset the LLMConfig
    LLMConfig.reset()


def test_app_config_attributes_masking(test_handler):
    logger, stream = test_handler
    app_config = AppConfig(
        e2b_api_key='e2b-xyz789', github_token='ghp_abcdefghijklmnopqrstuvwxyz'
    )
    logger.info(f'App Config: {app_config}')
    log_output = stream.getvalue()
    assert "e2b_api_key='******'" in log_output
    assert "github_token='******'" in log_output
    assert 'e2b-xyz789' not in log_output
    assert 'ghp_abcdefghijklmnopqrstuvwxyz' not in log_output

    # reset the AppConfig
    AppConfig.reset()


def test_sensitive_env_vars_masking(test_handler):
    logger, stream = test_handler
    sensitive_data = {
        'API_KEY': 'API_KEY_VALUE',
        'AWS_ACCESS_KEY_ID': 'AWS_ACCESS_KEY_ID_VALUE',
        'AWS_SECRET_ACCESS_KEY': 'AWS_SECRET_ACCESS_KEY_VALUE',
        'E2B_API_KEY': 'E2B_API_KEY_VALUE',
        'GITHUB_TOKEN': 'GITHUB_TOKEN_VALUE',
    }

    log_message = ' '.join(
        f"{attr}='{value}'" for attr, value in sensitive_data.items()
    )
    logger.info(log_message)

    log_output = stream.getvalue()
    for attr, value in sensitive_data.items():
        assert f"{attr}='******'" in log_output
        assert value not in log_output


def test_special_cases_masking(test_handler):
    logger, stream = test_handler
    sensitive_data = {
        'LLM_API_KEY': 'LLM_API_KEY_VALUE',
        'SANDBOX_ENV_GITHUB_TOKEN': 'SANDBOX_ENV_GITHUB_TOKEN_VALUE',
    }

    log_message = ' '.join(
        f"{attr}={value} with no single quotes' and something"
        for attr, value in sensitive_data.items()
    )
    logger.info(log_message)

    log_output = stream.getvalue()
    for attr, value in sensitive_data.items():
        assert f"{attr}='******'" in log_output
        assert value not in log_output
