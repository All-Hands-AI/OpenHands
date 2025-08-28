from openhands.core.message import Message
from openhands.router.base import ROUTER_REGISTRY, BaseRouter


class NoOpRouter(BaseRouter):
    ROUTER_NAME = 'noop_router'

    def get_active_llm(self, messages: list[Message]) -> str:
        # No-op router does not change the active LLM.
        return 'agent'


# Register the router
ROUTER_REGISTRY[NoOpRouter.ROUTER_NAME] = NoOpRouter
