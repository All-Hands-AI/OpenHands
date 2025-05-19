import uuid

from fastapi import Request

from openhands.events.event import Event
from openhands.server.shared import ConversationStoreImpl, config
from openhands.server.user_auth import get_user_auth
from openhands.storage.conversation.conversation_store import ConversationStore


async def get_conversation_store(request: Request) -> ConversationStore | None:
    conversation_store: ConversationStore | None = getattr(
        request.state, 'conversation_store', None
    )
    if conversation_store:
        return conversation_store
    user_auth = await get_user_auth(request)
    user_id = await user_auth.get_user_id()
    conversation_store = await ConversationStoreImpl.get_instance(config, user_id)
    request.state.conversation_store = conversation_store
    return conversation_store


def get_context_events(
    events: list[Event],
    event_id: int,
    context_size: int = 4,
) -> list[Event]:
    """
    Get a list of events around a specific event ID.

    Args:
        events: List of events to search through.
        event_id: The ID of the target event.
        context_size: Number of events to include before and after the target event.

    Returns:
        A list of events including the target event and the specified number of events before and after it.
    """
    target_event_index = None
    for i, event in enumerate(events):
        if event.id == event_id:
            target_event_index = i
            break

    if target_event_index is None:
        raise ValueError(f'Event with ID {event_id} not found in the event stream.')

    # Get X events around the target event
    start_index = max(0, target_event_index - context_size)
    end_index = min(
        len(events), target_event_index + context_size + 1
    )  # +1 to include the target event

    return events[start_index:end_index]


async def generate_unique_conversation_id(
    conversation_store: ConversationStore,
) -> str:
    conversation_id = uuid.uuid4().hex
    while await conversation_store.exists(conversation_id):
        conversation_id = uuid.uuid4().hex
    return conversation_id
