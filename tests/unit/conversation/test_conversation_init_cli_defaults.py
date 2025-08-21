from openhands.conversation.conversation import Conversation
from openhands.core.config import OpenHandsConfig
from openhands.llm.llm_registry import LLMRegistry
from openhands.storage import get_file_store


def test_conversation_init_cli_defaults(tmp_path):
    cfg = OpenHandsConfig(
        runtime='cli', file_store='local', file_store_path=str(tmp_path)
    )
    fs = get_file_store('local', str(tmp_path), None, None, False)
    llm_registry = LLMRegistry(cfg)
    c = Conversation('sid1', fs, cfg, llm_registry, user_id=None, headless_mode=True)
    assert c.sid == 'sid1'
    assert c.event_stream is not None
