from prompt_toolkit.styles import Style, merge_styles
from prompt_toolkit.styles.base import BaseStyle
from prompt_toolkit.styles.defaults import default_ui_style

# Centralized helper for CLI styles so we can safely merge our custom colors
# with prompt_toolkit's default UI style. This preserves completion menu and
# fuzzy-match visibility across different terminal themes (e.g., Ubuntu).

COLOR_GOLD = '#FFD700'
COLOR_GREY = '#808080'
COLOR_AGENT_BLUE = '#4682B4'  # Steel blue - readable on light/dark backgrounds


def get_cli_style() -> BaseStyle:
    base = default_ui_style()
    custom = Style.from_dict(
        {
            'gold': COLOR_GOLD,
            'grey': COLOR_GREY,
            'prompt': f'{COLOR_GOLD} bold',
            # Ensure good contrast for fuzzy matches on the selected completion row
            # across terminals/themes (e.g., Ubuntu GNOME, Alacritty, Kitty).
            # See https://github.com/OpenHands/OpenHands/issues/10330
            'completion-menu.completion.current fuzzymatch.outside': 'fg:#ffffff bg:#888888',
            'selected': COLOR_GOLD,
            'risk-high': '#FF0000 bold',  # Red bold for HIGH risk
            'placeholder': '#888888 italic',
        }
    )
    return merge_styles([base, custom])
