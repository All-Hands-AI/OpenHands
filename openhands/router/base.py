from abc import ABC, abstractmethod


class BaseRouter(ABC):
    @abstractmethod
    def should_route_to_custom_model(self, prompt: str) -> bool:
        pass
