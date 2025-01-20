import os

from fastapi import FastAPI, HTTPException

from openhands.core.logger import openhands_logger as logger
from openhands.server.middleware import (
    AttachConversationMiddleware,
    InMemoryRateLimiter,
    LocalhostCORSMiddleware,
    NoCacheMiddleware,
    RateLimitMiddleware,
)
from openhands.server.types import AppMode, OpenhandsConfigInterface
from openhands.utils.import_utils import get_impl


class OpenhandsConfig(OpenhandsConfigInterface):
    config_cls = os.environ.get('OPENHANDS_CONFIG_CLS', None)
    app_mode = AppMode.OSS
    posthog_client_key = 'phc_3ESMmY9SgqEAGBB6sMGK5ayYHkeUuknH2vP6FmWH9RA'
    github_client_id = os.environ.get('GITHUB_APP_CLIENT_ID', '')
    settings_store_class: str = (
        'openhands.storage.settings.file_settings_store.FileSettingsStore'
    )
    conversation_store_class: str = (
        'openhands.storage.conversation.file_conversation_store.FileConversationStore'
    )

    def verify_config(self):
        if self.config_cls:
            raise ValueError('Unexpected config path provided')

    def verify_github_repo_list(self, installation_id: int | None):
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

    def attach_middleware(self, api: FastAPI) -> None:
        api.add_middleware(
            LocalhostCORSMiddleware,
            allow_credentials=True,
            allow_methods=['*'],
            allow_headers=['*'],
        )

        api.add_middleware(NoCacheMiddleware)
        api.add_middleware(
            RateLimitMiddleware,
            rate_limiter=InMemoryRateLimiter(requests=10, seconds=1),
        )
        api.middleware('http')(AttachConversationMiddleware)


def load_openhands_config():
    config_cls = os.environ.get('OPENHANDS_CONFIG_CLS', None)
    logger.info(f'Using config class {config_cls}')

    openhands_config_cls = get_impl(OpenhandsConfig, config_cls)
    openhands_config = openhands_config_cls()
    openhands_config.verify_config()

    return openhands_config
