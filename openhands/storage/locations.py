CONVERSATION_BASE_DIR = 'sessions'


def get_conversation_dir(sid: str) -> str:
    return f'{CONVERSATION_BASE_DIR}/{sid}/'


def get_conversation_events_dir(sid: str) -> str:
    return f'{get_conversation_dir(sid)}events/'


def get_conversation_event_file(sid: str, id: int) -> str:
    return f'{get_conversation_events_dir(sid)}{id}.json'


def get_conversation_metadata_file(sid: str) -> str:
    return f'{get_conversation_dir(sid)}metadata.json'
