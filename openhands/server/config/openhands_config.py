import os
from openhands.server.types import AppMode, OpenhandsConfigInterface
from openhands.utils.import_utils import import_from


class OpenhandsOssConfig(OpenhandsConfigInterface):
    CONFIG_PATH = os.environ.get('OPENHANDS_CONFIG_PATH', None)
    APP_MODE = AppMode.OSS
    POSTHOG_CLIENT_KEY = 'phc_3ESMmY9SgqEAGBB6sMGK5ayYHkeUuknH2vP6FmWH9RA'
    GITHUB_CLIENT_ID = os.environ.get('GITHUB_APP_CLIENT_ID', '')
    ATTACH_SESSION_MIDDLEWARE = 'openhands.server.middleware.AttachSessionMiddleware'

    def verify_config(self):
        if self.CONFIG_PATH:
            raise ValueError('Unexpected config path provided')

    async def github_auth(self):
        """
        Skip Github Auth for AppMode OSS
        """
        pass


def load_openhands_config():
    config_path = os.environ.get('OPENHANDS_CONFIG_PATH', None)
    if config_path:
        OpenhandsConfig = import_from(config_path)
    else:
        OpenhandsConfig = OpenhandsOssConfig()

    OpenhandsConfig.verify_config()

    return OpenhandsConfig
