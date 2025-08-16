"""
Custom thoughts dictionary that provides backward compatibility.
"""

from typing import Any


class ThoughtsDict(dict[str, str]):
    """
    A dictionary that stores thoughts with backward compatibility.

    This class allows the thoughts field to work as both a dictionary
    and maintain backward compatibility with string access patterns.

    Keys:
    - 'default': The main thought content (backward compatible)
    - 'reasoning_content': LiteLLM reasoning content
    """

    def __init__(self, *args, **kwargs):
        # Handle initialization from string (backward compatibility)
        if len(args) == 1 and isinstance(args[0], str):
            super().__init__({'default': args[0]})
        elif len(args) == 1 and isinstance(args[0], dict):
            # Ensure 'default' key exists
            data = args[0].copy()
            if 'default' not in data:
                data['default'] = ''
            super().__init__(data)
        else:
            super().__init__(*args, **kwargs)
            # Ensure 'default' key exists
            if 'default' not in self:
                self['default'] = ''

    def __str__(self) -> str:
        """Return the default thought for backward compatibility."""
        return self.get('default', '')

    def __bool__(self) -> bool:
        """Return True if any thought content exists."""
        return any(value.strip() for value in self.values())

    def __eq__(self, other: Any) -> bool:
        """Support comparison with strings for backward compatibility."""
        if isinstance(other, str):
            return str(self) == other
        return super().__eq__(other)

    def __ne__(self, other: Any) -> bool:
        """Support not-equal comparison with strings for backward compatibility."""
        return not self.__eq__(other)

    @classmethod
    def from_string(cls, thought: str) -> 'ThoughtsDict':
        """Create a ThoughtsDict from a string."""
        return cls({'default': thought})

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> 'ThoughtsDict':
        """Create a ThoughtsDict from a dictionary."""
        return cls(data)

    def set_default(self, thought: str) -> None:
        """Set the default thought."""
        self['default'] = thought

    def set_reasoning_content(self, reasoning: str) -> None:
        """Set the reasoning content from LiteLLM."""
        self['reasoning_content'] = reasoning

    def get_default(self) -> str:
        """Get the default thought."""
        return self.get('default', '')

    def get_reasoning_content(self) -> str:
        """Get the reasoning content."""
        return self.get('reasoning_content', '')

    def __reduce__(self):
        """Custom serialization for pickle/dataclass serialization."""
        # For backward compatibility, serialize as the default string
        return (str, (self.get_default(),))

    def __iadd__(self, other: str) -> 'ThoughtsDict':
        """Support += operator for string concatenation."""
        current_default = self.get_default()
        self.set_default(current_default + other)
        return self

    def __add__(self, other: str) -> str:
        """Support + operator for string concatenation."""
        return self.get_default() + other

    def __radd__(self, other: str) -> str:
        """Support reverse + operator for string concatenation."""
        return other + self.get_default()
