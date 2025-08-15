from openhands.conversation.conversation import Conversation
from openhands.core.config import OpenHandsConfig
from openhands.storage import get_file_store


def test_conversation_init_cli_defaults(tmp_path):
    cfg = OpenHandsConfig(runtime='cli', file_store='local', file_store_path=str(tmp_path))
    fs = get_file_store('local', str(tmp_path), None, None, False)
    c = Conversation('sid1', fs, cfg, user_id=None, headless_mode=True)
    assert c.sid == 'sid1'
    assert c.event_stream is not None
