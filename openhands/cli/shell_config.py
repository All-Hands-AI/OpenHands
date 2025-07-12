"""Shell configuration management for OpenHands CLI aliases.

This module provides a simplified, more maintainable approach to managing
shell aliases across different shell types and platforms.
"""

import platform
import re
from pathlib import Path
from typing import Optional

from jinja2 import Template

try:
    import shellingham
except ImportError:
    shellingham = None


class ShellConfigManager:
    """Manages shell configuration files and aliases across different shells."""

    # Shell configuration templates
    ALIAS_TEMPLATES = {
        'bash': Template("""
# OpenHands CLI aliases
alias openhands="{{ command }}"
alias oh="{{ command }}"
"""),
        'zsh': Template("""
# OpenHands CLI aliases
alias openhands="{{ command }}"
alias oh="{{ command }}"
"""),
        'fish': Template("""
# OpenHands CLI aliases
alias openhands="{{ command }}"
alias oh="{{ command }}"
"""),
        'powershell': Template("""
# OpenHands CLI aliases
function openhands { {{ command }} $args }
function oh { {{ command }} $args }
"""),
    }

    # Shell configuration file patterns
    SHELL_CONFIG_PATTERNS = {
        'bash': ['.bashrc', '.bash_profile'],
        'zsh': ['.zshrc'],
        'fish': ['.config/fish/config.fish'],
        'csh': ['.cshrc'],
        'tcsh': ['.tcshrc'],
        'ksh': ['.kshrc'],
        'powershell': [
            'Documents/PowerShell/Microsoft.PowerShell_profile.ps1',
            'Documents/WindowsPowerShell/Microsoft.PowerShell_profile.ps1',
            '.config/powershell/Microsoft.PowerShell_profile.ps1',
        ],
    }

    # Regex patterns for detecting existing aliases
    ALIAS_PATTERNS = {
        'bash': [
            r'^\s*alias\s+openhands\s*=',
            r'^\s*alias\s+oh\s*=',
        ],
        'zsh': [
            r'^\s*alias\s+openhands\s*=',
            r'^\s*alias\s+oh\s*=',
        ],
        'fish': [
            r'^\s*alias\s+openhands\s*=',
            r'^\s*alias\s+oh\s*=',
        ],
        'powershell': [
            r'^\s*function\s+openhands\s*\{',
            r'^\s*function\s+oh\s*\{',
        ],
    }

    def __init__(
        self, command: str = 'uvx --python 3.12 --from openhands-ai openhands'
    ):
        """Initialize the shell config manager.

        Args:
            command: The command that aliases should point to.
        """
        self.command = command
        self.is_windows = platform.system() == 'Windows'

    def detect_shell(self) -> Optional[str]:
        """Detect the current shell using shellingham.

        Returns:
            Shell name if detected, None otherwise.
        """
        if not shellingham:
            return None

        try:
            shell_name, _ = shellingham.detect_shell()
            return shell_name
        except Exception:
            return None

    def get_shell_config_path(self, shell: Optional[str] = None) -> Path:
        """Get the path to the shell configuration file.

        Args:
            shell: Shell name. If None, will attempt to detect.

        Returns:
            Path to the shell configuration file.
        """
        if shell is None:
            shell = self.detect_shell()

        home = Path.home()

        # Try to find existing config file for the detected shell
        if shell and shell in self.SHELL_CONFIG_PATTERNS:
            for config_file in self.SHELL_CONFIG_PATTERNS[shell]:
                config_path = home / config_file
                if config_path.exists():
                    return config_path

            # If no existing file found, return the first option
            return home / self.SHELL_CONFIG_PATTERNS[shell][0]

        # Fallback logic
        if self.is_windows:
            # Windows fallback to PowerShell
            ps_profile = (
                home / 'Documents' / 'PowerShell' / 'Microsoft.PowerShell_profile.ps1'
            )
            return ps_profile
        else:
            # Unix fallback to bash
            bashrc = home / '.bashrc'
            if bashrc.exists():
                return bashrc
            return home / '.bash_profile'

    def get_shell_type_from_path(self, config_path: Path) -> str:
        """Determine shell type from configuration file path.

        Args:
            config_path: Path to the shell configuration file.

        Returns:
            Shell type name.
        """
        path_str = str(config_path).lower()

        if 'powershell' in path_str:
            return 'powershell'
        elif '.zshrc' in path_str:
            return 'zsh'
        elif 'fish' in path_str:
            return 'fish'
        elif '.bashrc' in path_str or '.bash_profile' in path_str:
            return 'bash'
        else:
            return 'bash'  # Default fallback

    def aliases_exist(self, config_path: Optional[Path] = None) -> bool:
        """Check if OpenHands aliases already exist in the shell config.

        Args:
            config_path: Path to check. If None, will detect automatically.

        Returns:
            True if aliases exist, False otherwise.
        """
        if config_path is None:
            config_path = self.get_shell_config_path()

        if not config_path.exists():
            return False

        shell_type = self.get_shell_type_from_path(config_path)
        patterns = self.ALIAS_PATTERNS.get(shell_type, self.ALIAS_PATTERNS['bash'])

        try:
            with open(config_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            for pattern in patterns:
                if re.search(pattern, content, re.MULTILINE):
                    return True

            return False
        except Exception:
            return False

    def add_aliases(self, config_path: Optional[Path] = None) -> bool:
        """Add OpenHands aliases to the shell configuration.

        Args:
            config_path: Path to modify. If None, will detect automatically.

        Returns:
            True if successful, False otherwise.
        """
        if config_path is None:
            config_path = self.get_shell_config_path()

        # Check if aliases already exist
        if self.aliases_exist(config_path):
            return True

        try:
            # Ensure parent directory exists
            config_path.parent.mkdir(parents=True, exist_ok=True)

            # Get the appropriate template
            shell_type = self.get_shell_type_from_path(config_path)
            template = self.ALIAS_TEMPLATES.get(
                shell_type, self.ALIAS_TEMPLATES['bash']
            )

            # Render the aliases
            aliases_content = template.render(command=self.command)

            # Append to the config file
            with open(config_path, 'a', encoding='utf-8') as f:
                f.write(aliases_content)

            return True
        except Exception as e:
            print(f'Error adding aliases: {e}')
            return False

    def get_reload_command(self, config_path: Optional[Path] = None) -> str:
        """Get the command to reload the shell configuration.

        Args:
            config_path: Path to the config file. If None, will detect automatically.

        Returns:
            Command to reload the shell configuration.
        """
        if config_path is None:
            config_path = self.get_shell_config_path()

        shell_type = self.get_shell_type_from_path(config_path)

        if shell_type == 'zsh':
            return 'source ~/.zshrc'
        elif shell_type == 'fish':
            return 'source ~/.config/fish/config.fish'
        elif shell_type == 'powershell':
            return '. $PROFILE'
        else:  # bash and others
            if '.bash_profile' in str(config_path):
                return 'source ~/.bash_profile'
            else:
                return 'source ~/.bashrc'


# Convenience functions that use the ShellConfigManager
def add_aliases_to_shell_config() -> bool:
    """Add OpenHands aliases to the shell configuration."""
    manager = ShellConfigManager()
    return manager.add_aliases()


def aliases_exist_in_shell_config() -> bool:
    """Check if OpenHands aliases exist in the shell configuration."""
    manager = ShellConfigManager()
    return manager.aliases_exist()


def get_shell_config_path() -> Path:
    """Get the path to the shell configuration file."""
    manager = ShellConfigManager()
    return manager.get_shell_config_path()
