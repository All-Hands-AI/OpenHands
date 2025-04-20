import numpy as np
import sglang as sgl
from sglang import RuntimeEndpoint, assistant, set_default_backend, system, user
from tenacity import retry, stop_after_attempt, wait_random_exponential

from openhands.core.config import ModelRoutingConfig
from openhands.llm.llm import LLM
from openhands.router.base import BaseRouter
from openhands.router.cost_saving.prompt import (
    CLASSIFIER_SYSTEM_MESSAGE,
    CLASSIFIER_USER_MESSAGE,
)

set_default_backend(
    RuntimeEndpoint(
        base_url='https://onuug1q6jd24ou.r21.modal.host',
        api_key='ht-test-key',
    )
)


@sgl.function
def score_trajectory(s, trajectory, **kwargs):
    s += system(CLASSIFIER_SYSTEM_MESSAGE)
    s += user(CLASSIFIER_USER_MESSAGE.format(conversation=trajectory))
    s += assistant(
        sgl.gen(
            'answer',
            return_logprob=True,
            max_tokens=1,
            temperature=0.0,
            choices=['0', '1'],
            choices_method=sgl.token_length_normalized,
        )
    )


class ThresholdBasedCostSavingRouter(BaseRouter):
    WEAK_MODEL_CONFIG = 'weak_model'
    CPT_THRESHOLD = 0.4073334000459302

    def __init__(
        self,
        llm: LLM,
        routing_llms: dict[str, LLM],
        model_routing_config: ModelRoutingConfig,
    ):
        super().__init__(llm, routing_llms, model_routing_config)

        self._validate_model_routing_config(model_routing_config, routing_llms)

        self.weak_llm = routing_llms[self.WEAK_MODEL_CONFIG]
        self.routing_history: list[int] = []
        self.max_token_exceeded = False

    @retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(3))
    def should_route_to(self, prompt: str) -> LLM:
        if self.max_token_exceeded:
            self.routing_history.append(0)
            return self.llm

        state = score_trajectory(prompt)
        prob_0 = np.exp(state.get_meta_info('answer')['input_token_logprobs'][0][0][0])
        prob_1 = np.exp(state.get_meta_info('answer')['input_token_logprobs'][1][0][0])
        threshold = prob_1 / (prob_0 + prob_1)
        # print('CostSavingRouter prob_0:', prob_0)
        # print('CostSavingRouter prob_1:', prob_1)
        print('CostSavingRouter threshold:', threshold)

        if threshold < self.CPT_THRESHOLD:
            self.routing_history.append(0)
            return self.llm

        self.routing_history.append(1)
        return self.weak_llm

    def _validate_model_routing_config(
        self, model_routing_config: ModelRoutingConfig, routing_llms: dict[str, LLM]
    ):
        if self.WEAK_MODEL_CONFIG not in routing_llms:
            raise ValueError(
                f'Weak LLM config {model_routing_config.reasoning_llm_config_name} not found'
            )
