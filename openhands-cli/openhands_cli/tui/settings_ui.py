"""Interactive settings configuration UI for OpenHands CLI."""

from .settings import SettingsScreen


def run_settings_configuration(first_time: bool = False) -> None:
    """Run the settings configuration UI.
    
    Args:
        first_time: If True, show first-time setup wizard
    """
    screen = SettingsScreen()
    screen.run(first_time=first_time)