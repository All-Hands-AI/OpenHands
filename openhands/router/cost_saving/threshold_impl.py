from tenacity import retry, stop_after_attempt, wait_random_exponential

from openhands.core.config import ModelRoutingConfig
from openhands.llm.llm import LLM
from openhands.router.base import BaseRouter
from openhands.router.cost_saving.prompt import (
    CLASSIFIER_SYSTEM_MESSAGE,
    CLASSIFIER_USER_MESSAGE,
)
from transformers import AutoTokenizer
import requests

API_URL = "https://blc5ptpat6uzvg.r26.modal.host/classify"
TOKENIZER_NAME = "Qwen/Qwen2.5-Coder-1.5B-Instruct"
MODEL_NAME = "router-1.5b-claude-4-devstral"
tokenizer = AutoTokenizer.from_pretrained(TOKENIZER_NAME)

def post_http_request(payload: dict, api_url: str) -> requests.Response:
    """Send HTTP request to VLLM classification endpoint."""
    headers = {
        "Authorization": "Bearer ht-test-key",
        "Content-Type": "application/json",
    }
    response = requests.post(api_url, headers=headers, json=payload)
    return response

class ThresholdBasedCostSavingRouter(BaseRouter):
    WEAK_MODEL_CONFIG = 'weak_model'
    CPT_THRESHOLD = 0.5546875

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

    def should_route_to(self, prompt: str) -> LLM:
        if self.max_token_exceeded:
            self.routing_history.append(0)
            return self.llm

        threshold = self.score_trajectory(prompt)
        print('CostSavingRouter threshold:', threshold)

        if threshold < self.CPT_THRESHOLD:
            self.routing_history.append(0)
            return self.llm

        self.routing_history.append(1)
        return self.weak_llm

    @retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(3))
    def score_trajectory(self, trajectory, **kwargs):
        """Score the trajectory using the weak model."""
        convo = self.create_conversation_prompt(trajectory)
        prompt = tokenizer.apply_chat_template([convo], tokenize=False, add_generation_prompt=True)[0]

        payload = {
            "model": MODEL_NAME,
            "input": [prompt],
        }

        response = post_http_request(payload=payload, api_url=API_URL)
        response.raise_for_status()

        result = response.json()
        threshold = result['data'][0]['probs'][1] # Probability for class 1
        return threshold


    def create_conversation_prompt(self, trajectory: str) -> list:
        """Create conversation format for the tokenizer."""
        conversation = [
            {"role": "system", "content": CLASSIFIER_SYSTEM_MESSAGE},
            {"role": "user", "content": CLASSIFIER_USER_MESSAGE.format(conversation=trajectory)}
        ]
        return conversation

    def _validate_model_routing_config(
        self, model_routing_config: ModelRoutingConfig, routing_llms: dict[str, LLM]
    ):
        if self.WEAK_MODEL_CONFIG not in routing_llms:
            raise ValueError(
                f'Weak LLM config {model_routing_config.reasoning_llm_config_name} not found'
            )
