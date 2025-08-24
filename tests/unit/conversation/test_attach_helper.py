from openhands.conversation.api import attach_to_conversation
from openhands.core.config import OpenHandsConfig
from openhands.llm.llm_registry import LLMRegistry


def test_attach_to_conversation_returns_instance(tmp_path):
    cfg = OpenHandsConfig(file_store='local', file_store_path=str(tmp_path))
    llm_registry = LLMRegistry(cfg)
    conv = attach_to_conversation(cfg, 'abc123', llm_registry, user_id=None)
    assert conv.sid == 'abc123'
