import asyncio

from storage.proactive_conversation_store import ProactiveConversationStore

OLDER_THAN = 30  # 30 minutes


async def main():
    convo_store = ProactiveConversationStore()
    await convo_store.clean_old_convos(older_than_minutes=OLDER_THAN)


if __name__ == '__main__':
    asyncio.run(main())
