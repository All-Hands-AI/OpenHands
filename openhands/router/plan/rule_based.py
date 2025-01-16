from openhands.router.base import BaseRouter


class RuleBasedPlanRouter(BaseRouter):
    """
    Router that detects if the prompt contains the string "plan".
    """

    def should_route_to_custom_model(self, prompt: str) -> bool:
        # Returns True if the prompt contains the word "plan"
        return 'plan' in prompt
