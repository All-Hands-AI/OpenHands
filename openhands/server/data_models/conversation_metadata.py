from dataclasses import dataclass


@dataclass
class ConversationMetadata:
    conversation_id: str
    github_user_id: str
    selected_repository: str | None
