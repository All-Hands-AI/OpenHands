import os
from typing import Literal

from pydantic import BaseModel, Field


class CLIConfig(BaseModel):
    """Configuration for CLI-specific settings."""

    vi_mode: bool = Field(default=False)
    editor_mode: Literal['emacs', 'vi', 'auto'] = Field(default='auto')

    model_config = {'extra': 'forbid'}

    def get_effective_editor_mode(self) -> Literal['emacs', 'vi']:
        """Get the effective editor mode, resolving 'auto' based on environment."""
        if self.editor_mode == 'auto':
            # Check EDITOR environment variable for vi/vim/nvim
            editor = os.environ.get('EDITOR', '').lower()
            if any(vim in editor for vim in ['vi', 'vim', 'nvim']):
                return 'vi'
            return 'emacs'
        elif self.editor_mode in ['emacs', 'vi']:
            return self.editor_mode
        else:
            # Handle invalid modes by defaulting to emacs
            return 'emacs'

    def is_vi_mode(self) -> bool:
        """Check if vi mode should be enabled (for backward compatibility)."""
        return self.vi_mode or self.get_effective_editor_mode() == 'vi'
