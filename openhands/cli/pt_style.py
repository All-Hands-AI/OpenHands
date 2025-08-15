from prompt_toolkit.styles import Style, merge_styles
from prompt_toolkit.styles.defaults import default_ui_style

# Centralized helper for CLI styles so we can safely merge our custom colors
# with prompt_toolkit's default UI style. This preserves completion menu and
# fuzzy-match visibility across different terminal themes (e.g., Ubuntu).

COLOR_GOLD = '#FFD700'
COLOR_GREY = '#808080'
COLOR_AGENT_BLUE = '#4682B4'  # Steel blue - readable on light/dark backgrounds


def get_cli_style() -> Style:
    base = default_ui_style()
    custom = Style.from_dict(
        {
            'gold': COLOR_GOLD,
            'grey': COLOR_GREY,
            'prompt': f'{COLOR_GOLD} bold',
            # The following entries are mostly redundant because default_ui_style
            # already sets sane values. We keep them minimal on purpose to avoid
            # clutter and ensure high contrast on various themes.
            # 'completion-menu': 'bg:#bbbbbb #000000',
            # 'completion-menu.completion.current': 'reverse',
        }
    )
    return merge_styles([base, custom])
