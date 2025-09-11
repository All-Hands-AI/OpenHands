class ConversationEventStream:
    """
    Interface providing forward compatibility between the old EventStream and the new AgentSDK Conversation API.

    The new AgentSDK offers a list like object in it's state including events - As of 2025-09-10 Xingyao and
    Calvin are working on making this potentially backed by the file system to reduce memory load.
    """
