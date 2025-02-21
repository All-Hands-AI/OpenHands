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

    NUM_TURNS_GAP = 1

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
        self.routed_turns: list[int] = []
        self.cur_turn_num = 0

    def should_route_to(self, prompt: str) -> LLM:
        self.cur_turn_num += 1

        if self.cur_turn_num - max(self.routed_turns, default=0) < self.NUM_TURNS_GAP:
            return self.llm

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
        should_route = int(response['choices'][0]['message']['content'].strip()) == 1

        if should_route:
            self.routed_turns.append(self.cur_turn_num)
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
