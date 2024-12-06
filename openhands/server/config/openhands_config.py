import os

from fastapi import HTTPException

from openhands.server.types import AppMode, OpenhandsConfigInterface
from openhands.utils.import_utils import import_from


class OpenhandsConfig(OpenhandsConfigInterface):
    config_path = os.environ.get('OPENHANDS_CONFIG_PATH', None)
    app_mode = AppMode.OSS
    posthog_client_key = 'phc_3ESMmY9SgqEAGBB6sMGK5ayYHkeUuknH2vP6FmWH9RA'
    github_client_id = os.environ.get('GITHUB_APP_CLIENT_ID', '')
    attach_session_middleware_path = (
        'openhands.server.middleware.AttachSessionMiddleware'
    )

    def verify_config(self):
        if self.config_path:
            raise ValueError('Unexpected config path provided')

    def verify_github_repo_list(self, installation_id):
        if self.app_mode == AppMode.OSS and installation_id:
            raise HTTPException(
                status_code=400,
                detail='Unexpected installation ID',
            )

    def get_config(self):
        config = {
            'APP_MODE': self.app_mode,
            'GITHUB_CLIENT_ID': self.github_client_id,
            'POSTHOG_CLIENT_KEY': self.posthog_client_key,
        }

        return config

    async def github_auth(self, data: dict):
        """
        Skip Github Auth for AppMode OSS
        """
        pass


def load_openhands_config():
    config_path = os.environ.get('OPENHANDS_CONFIG_PATH', None)
    if config_path:
        openhands_config_cls = import_from(config_path)
    else:
        openhands_config_cls = OpenhandsConfig

    if not issubclass(openhands_config_cls, OpenhandsConfigInterface):
        raise TypeError(
            f"The provided configuration class '{openhands_config_cls.__name__}' "
            f'does not extend OpenhandsConfigInterface.'
        )

    openhands_config = openhands_config_cls()
    openhands_config.verify_config()

    return openhands_config
