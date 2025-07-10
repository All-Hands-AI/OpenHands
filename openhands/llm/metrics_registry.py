from typing import Callable
from uuid import uuid4

from openhands.core.config.llm_config import LLMConfig
from openhands.core.logger import openhands_logger as logger
from openhands.llm.llm import LLM
from openhands.llm.metrics import Metrics


class LLMRegistry:
    metrics_id = str(uuid4())
    service_to_llm: dict[str, LLM] = {}

    def __init__(self, conversation_id: str | None = None):
        self.conversation_id = conversation_id

    def register_llm(
        self,
        service_id: str,
        config: LLMConfig,
        retry_listener: Callable[[int, int], None] | None = None,
    ):
        logger.info(
            f'[Metrics registry {self.metrics_id}]: Registering service for {service_id}'
        )

        if service_id in self.service_to_llm:
            raise Exception(f'Registering duplicate LLM: {service_id}')

        llm = LLM(config=config, service_id=service_id, retry_listener=retry_listener)
        self.service_to_llm[service_id] = llm
        return llm

    def request_existing_service(
        self,
        service_id: str,
        config: LLMConfig,
        retry_listener: Callable[[int, int], None] | None = None,
    ):
        if service_id not in self.service_to_llm:
            raise Exception(f'LLM service does not exist {service_id}')
        existing_llm = self.service_to_llm[service_id]

        return LLM(
            config=config,
            service_id=service_id,
            metrics=existing_llm.metrics,
            retry_listener=retry_listener,
        )

    def get_combined_metrics(self) -> Metrics:
        total_metrics = Metrics()
        for llm in self.service_to_llm.values():
            total_metrics.merge(llm.metrics)

        return total_metrics

    def save_registry(self):
        pass

    def maybe_restore_registry(self):
        if not self.conversation_id:
            return
