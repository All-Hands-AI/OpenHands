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


class PlanRouter(BaseRouter):
    """
    Router that routes the prompt requiring plan generation to specialized reasoning models.
    """

    REASONING_MODEL: str = 'o1-preview-2024-09-12'

    def route(self, prompt: str) -> str:
        """
        Routes the prompt to the specialized reasoning model.

        Parameters:
        - prompt (str): the prompt to be routed

        Returns:
        - str: the response from the specialized reasoning model
        """
        return self.REASONING_MODEL

    def _requires_plan_generation(self, prompt: str) -> bool:
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
