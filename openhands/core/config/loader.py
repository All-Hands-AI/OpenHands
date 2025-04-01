from openhands.core.config.app_config import AppConfig

def get_config() -> AppConfig:
    """Get the current application configuration"""
    return AppConfig()  # Returns default config, can be enhanced later