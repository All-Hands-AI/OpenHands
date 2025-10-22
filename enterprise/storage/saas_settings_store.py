from __future__ import annotations

import uuid
from dataclasses import dataclass

from server.logger import logger
from sqlalchemy.orm import joinedload, sessionmaker
from storage.database import session_maker
from storage.org import Org
from storage.org_member import OrgMember
from storage.org_store import OrgStore
from storage.user import User
from storage.user_settings import UserSettings
from storage.user_store import UserStore

from openhands.core.config.openhands_config import OpenHandsConfig
from openhands.server.settings import Settings
from openhands.storage.settings.settings_store import SettingsStore as OssSettingsStore


@dataclass
class SaasSettingsStore(OssSettingsStore):
    user_id: str
    session_maker: sessionmaker
    config: OpenHandsConfig
    ENCRYPT_VALUES = ['llm_api_key', 'llm_api_key_for_byor', 'search_api_key']

    async def load(self) -> Settings | None:
        user = UserStore.get_user_by_id(self.user_id)
        if not user:
            # Check if we need to migrate from user_settings
            user_settings = None
            with session_maker() as session:
                user_settings = (
                    session.query(UserSettings)
                    .filter(
                        UserSettings.keycloak_user_id == self.user_id,
                        UserSettings.migration_status.is_(False),
                    )
                    .first()
                )
            if user_settings:
                user = await UserStore.migrate_user(self.user_id, user_settings)
            else:
                logger.error(f'User not found for ID {self.user_id}')
                return None

        org_id = user.current_org_id
        org_member: OrgMember = None
        for om in user.org_members:
            if om.org_id == org_id:
                org_member = om
                break
        if not org_member or not org_member.llm_api_key:
            return None
        org = OrgStore.get_org_by_id(org_id)
        if not org:
            logger.error(
                f'Org not found for ID {org_id} as the current org for user {self.user_id}'
            )
            return None
        kwargs = {
            **{
                normalized: getattr(org, c.name)
                for c in Org.__table__.columns
                if (
                    normalized := c.name.removeprefix('_default_')
                    .removeprefix('default_')
                    .lstrip('_')
                )
                in Settings.model_fields
            },
            **{
                normalized: getattr(user, c.name)
                for c in User.__table__.columns
                if (normalized := c.name.lstrip('_')) in Settings.model_fields
            },
        }
        kwargs['llm_api_key'] = org_member.llm_api_key
        if org_member.max_iterations:
            kwargs['max_iterations'] = org_member.max_iterations
        if org_member.llm_model:
            kwargs['llm_model'] = org_member.llm_model
        if org_member.llm_api_key_for_byor:
            kwargs['llm_api_key_for_byor'] = org_member.llm_api_key_for_byor
        if org_member.llm_base_url:
            kwargs['llm_base_url'] = org_member.llm_base_url

        settings = Settings(**kwargs)
        return settings

    async def store(self, item: Settings):
        # Call the static store method from SettingsStore
        with self.session_maker() as session:
            if not item:
                return None
            kwargs = item.model_dump(context={'expose_secrets': True})
            user = (
                session.query(User)
                .options(joinedload(User.org_members))
                .filter(User.id == uuid.UUID(self.user_id))
            ).first()

            if not user:
                # Check if we need to migrate from user_settings
                user_settings = None
                with session_maker() as session:
                    user_settings = (
                        session.query(UserSettings)
                        .filter(UserSettings.keycloak_user_id == self.user_id)
                        .first()
                    )
                if user_settings:
                    user = await UserStore.migrate_user(self.user_id, user_settings)
                else:
                    logger.error(f'User not found for ID {self.user_id}')
                    return None

            org_id = user.current_org_id
            org_member = None
            for om in user.org_members:
                if om.org_id == org_id:
                    org_member = om
                    break
            if not org_member or not org_member.llm_api_key:
                return None
            org = session.query(Org).filter(Org.id == org_id).first()
            if not org:
                logger.error(
                    f'Org not found for ID {org_id} as the current org for user {self.user_id}'
                )
                return None

            for model in (user, org, org_member):
                for key, value in kwargs.items():
                    if hasattr(model, key):
                        setattr(model, key, value)

            session.commit()

    @classmethod
    async def get_instance(
        cls,
        config: OpenHandsConfig,
        user_id: str,  # type: ignore[override]
    ) -> SaasSettingsStore:
        logger.debug(f'saas_settings_store.get_instance::{user_id}')
        return SaasSettingsStore(user_id, session_maker, config)
