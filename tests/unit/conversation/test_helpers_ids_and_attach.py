import pytest

from openhands.conversation.api import (
    generate_unique_conversation_id,
    get_conversation_metadata,
    get_conversation_store,
)
from openhands.core.config import OpenHandsConfig


@pytest.mark.asyncio
async def test_generate_unique_conversation_id_and_metadata(tmp_path):
    cfg = OpenHandsConfig(file_store='local', file_store_path=str(tmp_path))
    store = await get_conversation_store(cfg, user_id=None)
    cid1 = await generate_unique_conversation_id(store)
    cid2 = await generate_unique_conversation_id(store)
    assert cid1 != cid2
    # No metadata yet; requesting should raise
    with pytest.raises(FileNotFoundError):
        await get_conversation_metadata(store, cid1)
