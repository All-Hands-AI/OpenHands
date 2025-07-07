from enum import Enum

from openhands.llm.metrics import Metrics


class LLMService(Enum):
    AGENT = 'AGENT'
    CONDENSER = 'CONDENSER'
    DRAFT_LLM = 'DRAFT_LLM'


class MetricsRegistry:
    global_metrics: dict[LLMService, Metrics]

    def register_llm(self, service: LLMService, model_name: str = 'default'):
        if service in self.global_metrics:
            return self.global_metrics[service]

        self.global_metrics[service] = Metrics(model_name=model_name)
        return self.global_metrics[service]

    def save_metrics(self):
        pass

    def restore_metrics(self):
        pass

    def get_combined_metrics(self) -> Metrics:
        total_metrics = Metrics()
        for service in self.global_metrics:
            total_metrics.merge(self.global_metrics[service])

        return total_metrics
