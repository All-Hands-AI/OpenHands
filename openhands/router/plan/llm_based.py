import copy

from openhands.core.config import LLMConfig
from openhands.llm.llm import LLM
from openhands.router.base import BaseRouter
from openhands.router.plan.prompts import (
    TRAJECTORY_JUDGE_REASONING_SYSTEM_PROMPT,
    TRAJECTORY_JUDGE_REASONING_USER_PROMPT,
)


class LLMBasedPlanRouter(BaseRouter):
    """
    Router that routes the prompt that is judged by a LLM as complex and requires a step-by-step plan.
    """

    JUDGE_MODEL = 'gpt-4o'

    def __init__(self, llm_config: LLMConfig):
        super().__init__()

        judge_llm_config = copy.deepcopy(llm_config)
        self.judge_llm = LLM(judge_llm_config)

    def should_route_to_custom_model(self, prompt: str) -> bool:
        messages = [
            {
                'role': 'system',
                'content': TRAJECTORY_JUDGE_REASONING_SYSTEM_PROMPT,
            },
            {
                'role': 'user',
                'content': TRAJECTORY_JUDGE_REASONING_USER_PROMPT.format(
                    interaction_log=prompt
                ),
            },
        ]

        response = self.judge_llm.completion(
            messages=messages,
            model=self.JUDGE_MODEL,
        )
        return int(response['choices'][0]['message']['content'].strip()) == 1
