---
sidebar_label: llm
title: opendevin.llm.llm
---

## LLM Objects

```python
class LLM()
```

The LLM class represents a Language Model instance.

#### \_\_init\_\_

```python
def __init__(model=DEFAULT_MODEL_NAME,
             api_key=DEFAULT_API_KEY,
             base_url=DEFAULT_BASE_URL,
             api_version=DEFAULT_API_VERSION,
             num_retries=LLM_NUM_RETRIES,
             retry_min_wait=LLM_RETRY_MIN_WAIT,
             retry_max_wait=LLM_RETRY_MAX_WAIT,
             llm_timeout=LLM_TIMEOUT,
             llm_max_return_tokens=LLM_MAX_RETURN_TOKENS)
```

**Arguments**:

- `model` _str, optional_ - The name of the language model. Defaults to LLM_MODEL.
- `api_key` _str, optional_ - The API key for accessing the language model. Defaults to LLM_API_KEY.
- `base_url` _str, optional_ - The base URL for the language model API. Defaults to LLM_BASE_URL. Not necessary for OpenAI.
- `api_version` _str, optional_ - The version of the API to use. Defaults to LLM_API_VERSION. Not necessary for OpenAI.
- `num_retries` _int, optional_ - The number of retries for API calls. Defaults to LLM_NUM_RETRIES.
- `retry_min_wait` _int, optional_ - The minimum time to wait between retries in seconds. Defaults to LLM_RETRY_MIN_TIME.
- `retry_max_wait` _int, optional_ - The maximum time to wait between retries in seconds. Defaults to LLM_RETRY_MAX_TIME.
- `llm_timeout` _int, optional_ - The maximum time to wait for a response in seconds. Defaults to LLM_TIMEOUT.
- `llm_max_return_tokens` _int, optional_ - The maximum number of tokens to return. Defaults to LLM_MAX_RETURN_TOKENS.
  

**Attributes**:

- `model_name` _str_ - The name of the language model.
- `api_key` _str_ - The API key for accessing the language model.
- `base_url` _str_ - The base URL for the language model API.
- `api_version` _str_ - The version of the API to use.

#### completion

```python
@property
def completion()
```

Decorator for the litellm completion function.

