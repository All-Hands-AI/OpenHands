import os

from openai import OpenAI


# ==================================================================================================
# OPENAI
# TODO: Move this to EventStream Actions when DockerRuntime is fully implemented
# NOTE: we need to get env vars inside functions because they will be set in IPython
# AFTER the agentskills is imported (the case for DockerRuntime)
# ==================================================================================================
def _get_openai_api_key():
    return os.getenv('OPENAI_API_KEY', os.getenv('SANDBOX_ENV_OPENAI_API_KEY', ''))


def _get_openai_base_url():
    return os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')


def _get_openai_model():
    return os.getenv('OPENAI_MODEL', 'gpt-4o')


def _get_max_token():
    return os.getenv('MAX_TOKEN', 500)


def _get_openai_client():
    client = OpenAI(api_key=_get_openai_api_key(), base_url=_get_openai_base_url())
    return client
