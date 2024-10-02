

from dataclasses import dataclass
from typing import Literal
from oh.event.detail.event_detail_abc import EventDetailABC


@dataclass
class TextReply(EventDetailABC):
    """ A Text reply from the agent. """
    text: str
    type: Literal["TextReply"] = "TextReply"
