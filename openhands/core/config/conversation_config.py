from pydantic import BaseModel, Field, ValidationError


class ConversationConfig(BaseModel):
    enable_streaming: bool = Field(default=False)

    @classmethod
    def from_toml_section(cls, data: dict) -> dict[str, 'ConversationConfig']:
        """Create a mapping of ConversationConfig instances from a toml dictionary representing the [conversation] section."""
        conversation_mapping: dict[str, ConversationConfig] = {}
        try:
            conversation_mapping['conversation'] = cls.model_validate(data)
        except ValidationError as e:
            raise ValueError(f'Invalid conversation configuration: {e}')

        return conversation_mapping
