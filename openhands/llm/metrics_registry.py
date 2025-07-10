from uuid import uuid4

from openhands.core.config.llm_config import LLMConfig
from openhands.core.logger import openhands_logger as logger
from openhands.llm.llm import LLM
from openhands.llm.metrics import Metrics


class LLMRegistry:
    metrics_id = str(uuid4())
    service_to_llm: dict[str, LLM] = {}

    def register_llm(self, service_id: str, config: LLMConfig):
        logger.info(
            f'[Metrics registry {self.metrics_id}]: Registering service for {service_id}'
        )

        if service_id in self.service_to_llm:
            raise Exception(f'Registering duplicate LLM: {service_id}')

        llm = LLM(config=config)
        self.service_to_llm[service_id] = llm
        return llm

    def get_shared_llm(self, service_id: str):
        if service_id not in self.service_to_llm:
            raise Exception(f'LLM service does not exist {service_id}')

        return self.service_to_llm[service_id]

    def get_combined_metrics(self) -> Metrics:
        total_metrics = Metrics()
        for llm in self.service_to_llm.values():
            total_metrics.merge(llm.metrics)

        return total_metrics
