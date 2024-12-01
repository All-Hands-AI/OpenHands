import os
import sys
import time

from openai import OpenAI
from tenacity import (
    retry,
    stop_after_attempt,  # type: ignore
    wait_random_exponential,  # type: ignore
)

if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal


Model = Literal['gpt-4', 'gpt-3.5-turbo', 'text-davinci-003']

OpenAI.api_key = os.getenv('OPENAI_API_KEY')
OPENAI_GEN_HYP = {
    'temperature': 0,
    'max_tokens': 250,
    'top_p': 1.0,
    'frequency_penalty': 0,
    'presence_penalty': 0,
}


@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
def run_chatgpt_query_multi_turn(
    messages,
    model_name='gpt-4-turbo',  # pass "gpt4" for more recent model output
    max_tokens=256,
    temperature=0.0,
    json_response=False,
):
    response = None
    num_retries = 3
    retry = 0
    while retry < num_retries:
        retry += 1
        try:
            client = OpenAI()

            if json_response:
                response = client.chat.completions.create(
                    model=model_name,
                    response_format={'type': 'json_object'},
                    messages=messages,
                    **OPENAI_GEN_HYP,
                )
            else:
                response = client.chat.completions.create(
                    model=model_name, messages=messages, **OPENAI_GEN_HYP
                )
            break

        except Exception as e:
            print(e)
            print('GPT error. Retrying in 2 seconds...')
            time.sleep(2)

    return response
