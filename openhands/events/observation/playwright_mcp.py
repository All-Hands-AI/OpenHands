from dataclasses import dataclass, field

from openhands.core.schema import ObservationType
from openhands.events.observation.observation import Observation


@dataclass
class PlaywrightMcpBrowserScreenshotObservation(Observation):
    """This data class represents the result of a Playwright MCP Browser Screenshot operation.

    The response is a dict {"data": "base64 encoded string of the screenshot, which should be streamed to the client using the correct format matching
    browsergym's screenshot format", "url": "url of the current webpage"}.
    """

    url: str
    trigger_by_action: str
    observation: str = ObservationType.PLAYWRIGHT_MCP_BROWSER_SCREENSHOT
    screenshot: str = field(repr=False, default='')  # don't show in repr

    @property
    def message(self) -> str:
        return self.content
