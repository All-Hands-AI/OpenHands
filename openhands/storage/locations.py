import re

CONVERSATION_BASE_DIR = 'sessions'


def get_conversation_dir(sid: str, user_id: str | None = None) -> str:
    if user_id:
        return f'users/{user_id}/conversations/{sid}/'
    else:
        return f'{CONVERSATION_BASE_DIR}/{sid}/'


def get_conversation_events_dir(sid: str, user_id: str | None = None) -> str:
    return f'{get_conversation_dir(sid, user_id)}events/'


def get_conversation_event_filename(
    sid: str, id: int, user_id: str | None = None
) -> str:
    return f'{get_conversation_events_dir(sid, user_id)}{id}.json'


def get_conversation_metadata_filename(sid: str, user_id: str | None = None) -> str:
    return f'{get_conversation_dir(sid, user_id)}metadata.json'


def get_conversation_init_data_filename(sid: str, user_id: str | None = None) -> str:
    return f'{get_conversation_dir(sid, user_id)}init.json'


def get_conversation_agent_state_filename(sid: str, user_id: str | None = None) -> str:
    return f'{get_conversation_dir(sid, user_id)}agent_state.pkl'


def parse_conversation_path(path: str) -> dict | None:
    """
    Extract user_id, session_id, event_id (if present), and type from a given path.
    Returns a dict with keys: user_id, session_id, event_id, type
    """
    # User-specific patterns
    list_user_events_pattern = re.compile(
        r'^users/(?P<user_id>[^/]+)/conversations/(?P<session_id>[^/]+)/events/$'
    )

    user_event_pattern = re.compile(
        r'^users/(?P<user_id>[^/]+)/conversations/(?P<session_id>[^/]+)/events/(?P<event_id>\d+)\.json$'
    )
    user_metadata_pattern = re.compile(
        r'^users/(?P<user_id>[^/]+)/conversations/(?P<session_id>[^/]+)/metadata\.json$'
    )
    user_init_pattern = re.compile(
        r'^users/(?P<user_id>[^/]+)/conversations/(?P<session_id>[^/]+)/init\.json$'
    )
    user_agent_state_pattern = re.compile(
        r'^users/(?P<user_id>[^/]+)/conversations/(?P<session_id>[^/]+)/agent_state\.pkl$'
    )
    user_settings_pattern = re.compile(r'^users/(?P<user_id>[^/]+)/settings\.json$')

    # Non-user-specific patterns
    list_events_pattern = re.compile(r'^sessions/(?P<session_id>[^/]+)/events/$')
    event_pattern = re.compile(
        r'^sessions/(?P<session_id>[^/]+)/events/(?P<event_id>\d+)\.json$'
    )
    metadata_pattern = re.compile(r'^sessions/(?P<session_id>[^/]+)/metadata\.json$')
    init_pattern = re.compile(r'^sessions/(?P<session_id>[^/]+)/init\.json$')
    agent_state_pattern = re.compile(
        r'^sessions/(?P<session_id>[^/]+)/agent_state\.pkl$'
    )

    patterns = [
        (user_event_pattern, 'events'),
        (user_metadata_pattern, 'metadata'),
        (user_init_pattern, 'init'),
        (user_agent_state_pattern, 'agent_state'),
        (user_settings_pattern, 'settings'),
        (event_pattern, 'events'),
        (metadata_pattern, 'metadata'),
        (init_pattern, 'init'),
        (agent_state_pattern, 'agent_state'),
        (list_user_events_pattern, 'events'),
        (list_events_pattern, 'events'),
    ]

    for pattern, typ in patterns:
        m = pattern.match(path)
        if m:
            d = m.groupdict()
            return {
                'user_id': d.get('user_id'),
                'session_id': d.get('session_id'),
                'event_id': int(d['event_id'])
                if 'event_id' in d and d['event_id'] is not None
                else None,
                'type': typ,
            }
    # If no pattern matches, return None or raise error
    return None
