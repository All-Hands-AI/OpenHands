"""
Store class for managing organizations.
"""

from typing import Optional
from uuid import UUID

from enterprise.server.constants import ORG_SETTINGS_VERSION, get_default_litellm_model
from sqlalchemy.orm import Session, joinedload
from enterprise.storage.database import session_maker
from enterprise.storage.lite_llm_manager import LiteLlmManager
from enterprise.storage.org import Org
from enterprise.storage.user import User

from openhands.core.logger import openhands_logger as logger
from openhands.storage.data_models.settings import Settings
from openhands.utils.async_utils import call_async_from_sync


class OrgStore:
    """Store for managing organizations."""

    @staticmethod
    def create_org(
        kwargs: dict,
    ) -> Org:
        """Create a new organization."""
        with session_maker() as session:
            org = Org(**kwargs)
            OrgStore.migrate_org(None, org)
            session.add(org)
            session.commit()
            session.refresh(org)
            return org

    @staticmethod
    def get_org_by_id(org_id: UUID) -> Optional[Org]:
        """Get organization by ID."""
        with session_maker() as session:
            return OrgStore.migrate_org(
                session, session.query(Org).filter(Org.id == org_id).first()
            )

    @staticmethod
    def get_current_org_from_keycloak_user_id(keycloak_user_id: str) -> Optional[Org]:
        with session_maker() as session:
            user = (
                session.query(User)
                .options(joinedload(User.org_users))
                .filter(User.keycloak_user_id == keycloak_user_id)
                .first()
            )
            if not user:
                logger.warning(f'User not found for ID {keycloak_user_id}')
                return None
            org_id = user.current_org_id
            org = OrgStore.migrate_org(
                session, session.query(Org).filter(Org.id == org_id).first()
            )
            if not org:
                logger.warning(
                    f'Org not found for ID {org_id} as the current org for user {keycloak_user_id}'
                )
                return None
            return org

    @staticmethod
    def get_org_by_name(name: str) -> Optional[Org]:
        """Get organization by name."""
        with session_maker() as session:
            return OrgStore.migrate_org(
                session, session.query(Org).filter(Org.name == name).first()
            )

    @staticmethod
    def list_orgs() -> list[Org]:
        """List all organizations."""
        with session_maker() as session:
            orgs = session.query(Org).all()
            return [OrgStore.migrate_org(session, org) for org in orgs]

    @staticmethod
    def update_org(
        org_id: UUID,
        kwargs: dict,
    ) -> Optional[Org]:
        """Update organization details."""
        with session_maker() as session:
            org = session.query(Org).filter(Org.id == org_id).first()
            if not org:
                return None

            if 'org_id' in kwargs:
                kwargs.pop('org_id')
            for key, value in kwargs.items():
                if hasattr(org, key):
                    setattr(org, key, value)

            OrgStore.migrate_org(None, org)

            session.commit()
            session.refresh(org)
            return org

    @staticmethod
    def get_kwargs_from_settings(settings: Settings):
        kwargs = {
            c.name: getattr(settings, c.name)
            for c in Org.__table__.columns
            if hasattr(settings, c.name)
        }
        return kwargs

    @staticmethod
    def migrate_org(
        session: Session | None,
        org: Org,
    ):
        """Create a new organization."""
        if not org or org.org_version == ORG_SETTINGS_VERSION:
            return org
        call_async_from_sync(
            LiteLlmManager.update_team,
            team_id=str(org.id),
            team_alias=None,
            max_budget=None,
        )
        org.org_version = ORG_SETTINGS_VERSION
        org.llm_model = get_default_litellm_model()
        if session:
            session.commit()
            session.refresh(org)
        return org
