class ConversationValidator:
    """Storage for conversation metadata. May or may not support multiple users depending on the environment."""

    async def validate(self, conversation_id: str, cookies_str: str):
        return None, None
