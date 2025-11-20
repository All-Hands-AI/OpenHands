import logging
from uuid import UUID

from openhands.app_server.event_callback.event_callback_models import (
    EventCallback,
    EventCallbackProcessor,
)
from openhands.app_server.event_callback.event_callback_result_models import (
    EventCallbackResult,
    EventCallbackResultStatus,
)
from openhands.sdk import Event

from openhands.core.schema.agent import AgentState
from openhands.events.observation.agent import AgentStateChangedObservation

_logger = logging.getLogger(__name__)


class GithubV1CallbackProcessor(EventCallbackProcessor):
    """Callback processor for GitHub V1 integrations."""

    github_view_data: dict
    send_summary_instruction: bool = True

    async def __call__(
        self,
        conversation_id: UUID,
        callback: EventCallback,
        event: Event,
    ) -> EventCallbackResult | None:
        """Process events for GitHub V1 integration."""

        if not isinstance(event, AgentStateChangedObservation):
            return None


        if event.agent_state not in (
            AgentState.AWAITING_USER_INPUT,
            AgentState.FINISHED,
        ):
            return None



        _logger.info(f'[GitHub V1] Callback agent state was {event.agent_state}')

        # TODO: Implement GitHub integration logic here
        # 1. Make sure this class has a reference to the agent_server ID, etc
        # 2. Send message to conversation via conversation manager perhaps

        # For now, just return success
        return EventCallbackResult(
            status=EventCallbackResultStatus.SUCCESS,
            event_callback_id=callback.id,
            event_id=event.id,
            conversation_id=conversation_id,
        )
