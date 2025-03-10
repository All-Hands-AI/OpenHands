from dataclasses import dataclass, field

from openhands.storage.data_models.user_secret import UserSecret


@dataclass
class UserSecretResultSet:
    results: list[UserSecret] = field(default_factory=list)
    next_page_id: str | None = None
