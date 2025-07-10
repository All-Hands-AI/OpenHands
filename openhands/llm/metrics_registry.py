from enum import Enum
from uuid import uuid4

from openhands.core.logger import openhands_logger as logger
from openhands.llm.metrics import Metrics


class LLMService(Enum):
    AGENT = 'AGENT'
    CONDENSER = 'CONDENSER'
    DRAFT_LLM = 'DRAFT_LLM'
    CONVO_TITLE_CREATOR = 'CONVO_TITLE_CREATOR'


class MetricsRegistry:
    metrics_id = str(uuid4())
    global_metrics: dict[LLMService, Metrics] = {}

    def register_llm(self, service: LLMService, model_name: str = 'default'):
        logger.info(
            f'[Metrics registry {self.metrics_id}]: Registering service {service}'
        )

        if service in self.global_metrics:
            return self.global_metrics[service]

        metrics = Metrics(model_name=model_name)
        self.global_metrics[service] = metrics
        return metrics

    def save_metrics(self):
        pass

    def get_combined_metrics(self) -> Metrics:
        print('all metrics', self.global_metrics)
        total_metrics = Metrics()
        for service in self.global_metrics:
            total_metrics.merge(self.global_metrics[service])

        return total_metrics
