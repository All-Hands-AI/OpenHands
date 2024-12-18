SESSION_BASE_DIR = 'sessions/'


def get_session_dir(sid: str) -> str:
    return f'{SESSION_BASE_DIR}{sid}/'


def get_session_events_dir(sid: str) -> str:
    return f'{get_session_dir(sid)}events/'


def get_session_event_file(sid: str, id: int) -> str:
    return f'{get_session_events_dir(sid)}{id}.json'
