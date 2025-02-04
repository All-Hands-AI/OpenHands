from openhands.core.config import ModelRoutingConfig
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

    def __init__(
        self,
        llm: LLM,
        routing_llms: dict[str, LLM],
        model_routing_config: ModelRoutingConfig,
    ):
        super().__init__(llm, routing_llms, model_routing_config)

        self._validate_model_routing_config(model_routing_config, routing_llms)

        self.judge_llm = routing_llms[model_routing_config.judge_llm_config_name]
        self.reasoning_llm = routing_llms[
            model_routing_config.reasoning_llm_config_name
        ]

    def should_route_to(self, prompt: str) -> LLM:
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
        )
        if int(response['choices'][0]['message']['content'].strip()) == 1:
            return self.reasoning_llm
        return self.llm

    def _validate_model_routing_config(
        self, model_routing_config: ModelRoutingConfig, routing_llms: dict[str, LLM]
    ):
        if (
            not model_routing_config.judge_llm_config_name
            or not model_routing_config.reasoning_llm_config_name
        ):
            raise ValueError(
                'Judge LLM and Reasoning LLM config names must be provided'
            )
        if model_routing_config.judge_llm_config_name not in routing_llms:
            raise ValueError(
                f'Judge LLM config {model_routing_config.judge_llm_config_name} not found'
            )
        if model_routing_config.reasoning_llm_config_name not in routing_llms:
            raise ValueError(
                f'Reasoning LLM config {model_routing_config.reasoning_llm_config_name} not found'
            )
