CONVERSATION_BASE_DIR = 'sessions'


def get_conversation_dir(conversation_id: str, user_id: str | None = None) -> str:
    if user_id:
        return f'users/{user_id}/conversations/{conversation_id}/'
    else:
        return f'{CONVERSATION_BASE_DIR}/{conversation_id}/'


def get_conversation_events_dir(
    conversation_id: str, user_id: str | None = None
) -> str:
    return f'{get_conversation_dir(conversation_id, user_id)}events/'


def get_conversation_event_filename(
    conversation_id: str, id: int, user_id: str | None = None
) -> str:
    return f'{get_conversation_events_dir(conversation_id, user_id)}{id}.json'


def get_conversation_metadata_filename(
    conversation_id: str, user_id: str | None = None
) -> str:
    return f'{get_conversation_dir(conversation_id, user_id)}metadata.json'


def get_conversation_init_data_filename(
    conversation_id: str, user_id: str | None = None
) -> str:
    return f'{get_conversation_dir(conversation_id, user_id)}init.json'


def get_conversation_agent_state_filename(
    conversation_id: str, user_id: str | None = None
) -> str:
    return f'{get_conversation_dir(conversation_id, user_id)}agent_state.pkl'
