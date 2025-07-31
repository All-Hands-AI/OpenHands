from pydantic import BaseModel, ConfigDict, Field, ValidationError


class ApprovedCommandPattern(BaseModel):
    """Configuration for an approved command pattern.

    Attributes:
        pattern: The regex pattern to match commands against.
        description: A human-readable description of what this pattern matches.
    """

    pattern: str
    description: str


class SecurityConfig(BaseModel):
    """Configuration for security related functionalities.

    Attributes:
        confirmation_mode: Whether to enable confirmation mode.
        security_analyzer: The security analyzer to use.
        approved_command_patterns: List of approved command patterns that don't require confirmation.
        approved_commands: Dictionary of exact commands that have been approved.
    """

    confirmation_mode: bool = Field(default=False)
    security_analyzer: str | None = Field(default=None)
    approved_command_patterns: list[ApprovedCommandPattern] = Field(
        default_factory=list
    )
    approved_commands: dict[str, bool] = Field(default_factory=dict)

    model_config = ConfigDict(extra='forbid')
    
    def is_command_approved(self, command: str) -> bool:
        """Check if a command is approved.
        
        This is a stub method that always returns False.
        The actual implementation is in CommandApprovalAnalyzer.
        
        Args:
            command: The command to check.
            
        Returns:
            bool: Always False in this stub implementation.
        """
        return False

    @classmethod
    def from_toml_section(cls, data: dict) -> dict[str, 'SecurityConfig']:
        """
        Create a mapping of SecurityConfig instances from a toml dictionary representing the [security] section.

        The configuration is built from all keys in data.

        Returns:
            dict[str, SecurityConfig]: A mapping where the key "security" corresponds to the [security] configuration
        """

        # Initialize the result mapping
        security_mapping: dict[str, SecurityConfig] = {}

        # Extract approved command patterns if present
        approved_patterns = []
        if 'approved_command_patterns' in data:
            patterns_data = data.pop('approved_command_patterns')
            if isinstance(patterns_data, list):
                for pattern_data in patterns_data:
                    if (
                        isinstance(pattern_data, dict)
                        and 'pattern' in pattern_data
                        and 'description' in pattern_data
                    ):
                        approved_patterns.append(
                            ApprovedCommandPattern(
                                pattern=pattern_data['pattern'],
                                description=pattern_data['description'],
                            )
                        )

        # Extract approved commands if present
        approved_commands = {}
        if 'approved_commands' in data:
            commands_data = data.pop('approved_commands')
            if isinstance(commands_data, dict):
                approved_commands = commands_data

        # Try to create the configuration instance
        try:
            config = cls.model_validate(data)
            config.approved_command_patterns = approved_patterns
            config.approved_commands = approved_commands
            security_mapping['security'] = config
        except ValidationError as e:
            raise ValueError(f'Invalid security configuration: {e}')

        return security_mapping
