from enum import Enum
from openhands.llm.metrics import Metrics
from openhands.core.logger import openhands_logger as logger

class LLMService(Enum):
    AGENT = 'AGENT'
    CONDENSER = 'CONDENSER'
    DRAFT_LLM = 'DRAFT_LLM'


class MetricsRegistry:
    global_metrics: dict[LLMService, Metrics]

    def register_llm(self, service: LLMService):
        if service in self.global_metrics:
            logger.warning(f'Service {service} is already registered')
            return

        self.global_metrics[service] = Metrics()

    def accumulate_metrics(self, service: LLMService, metrics: Metrics):
        if service not in self.global_metrics:
            logger.error(f'Service {service} does not exist in metrics registry')

        self.global_metrics[service].merge(metrics)

    def save_metrics(self):
        pass


    def restore_metrics(self):
        pass


    def get_combined_metrics(self) -> Metrics:
        total_metrics = Metrics()
        for service in self.global_metrics:
            total_metrics.merge(self.global_metrics[service])

        return total_metrics

