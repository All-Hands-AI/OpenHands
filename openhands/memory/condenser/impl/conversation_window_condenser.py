from __future__ import annotations

from openhands.events.action.agent import CondensationAction, CondensationRequestAction
from openhands.memory.condenser.condenser import RollingCondenser, View, Condensation
from openhands.core.config.condenser_config import ConversationWindowCondenserConfig

class ConversationWindowCondenser(RollingCondenser):
    def __init__(self) -> None:
        super().__init__()

    def get_condensation(self, view: View) -> Condensation:
        raise NotImplementedError()

    def should_condense(self, view: View) -> bool:
        # Should condense if there's a condensation request action with no condensation afterwards
        has_condensed: bool = False
        for event in reversed(view):
            if isinstance(event, CondensationRequestAction):
                return not has_condensed
            if isinstance(event, CondensationAction):
                has_condensed = True
        return False

    @classmethod
    def from_config(cls, config: ConversationWindowCondenserConfig) -> ConversationWindowCondenser:
        return ConversationWindowCondenser()

ConversationWindowCondenser.register_config(ConversationWindowCondenserConfig)
