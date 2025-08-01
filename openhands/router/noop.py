from openhands.core.message import Message
from openhands.events.event import Event
from openhands.router.base import ROUTER_REGISTRY, BaseRouter


class NoOpRouter(BaseRouter):
    ROUTER_NAME = 'noop_router'

    def set_active_llm(self, messages: list[Message], events: list[Event]) -> None:
        """No-op router does not change the active LLM."""
        self.routing_history.append(0)


# Register the router
ROUTER_REGISTRY[NoOpRouter.ROUTER_NAME] = NoOpRouter
