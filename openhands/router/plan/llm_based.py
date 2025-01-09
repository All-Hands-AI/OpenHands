import os
from os import path

from dotenv import load_dotenv
from litellm import completion

from openhands.router.base import BaseRouter
from openhands.router.plan.prompts import ANALYZE_PROMPT

# Load the environment variables
dotenv_path = path.join(path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

litellm_config = {
    'model': os.environ['LITELLM_MODEL'],
    'api_key': os.environ['LITELLM_API_KEY'],
    'base_url': os.environ['LITELLM_BASE_URL'],
}


class LLMBasedPlanRouter(BaseRouter):
    """
    Router that routes the prompt that is judged by a LLM as complex and requires a step-by-step plan.
    """

    def should_route_to_custom_model(self, prompt: str) -> bool:
        messages = []

        messages.append(
            {
                'role': 'user',
                'content': ANALYZE_PROMPT.format(message=prompt),
            }
        )

        response = completion(
            messages=messages,
            **litellm_config,
            temperature=0.0,
            max_tokens=10,
            stream=False,
        )
        return int(response['choices'][0]['message']['content'].strip()) == 1
