"""
Store class for managing users.
"""

from typing import Optional

from enterprise.integrations.stripe_service import migrate_customer
from enterprise.server.logger import logger
from sqlalchemy.orm import joinedload
from enterprise.storage.database import session_maker
from enterprise.storage.encrypt_utils import decrypt_model
from enterprise.storage.lite_llm_manager import LiteLlmManager
from enterprise.storage.org import Org
from enterprise.storage.org_store import OrgStore
from enterprise.storage.org_user import OrgUser
from enterprise.storage.role_store import RoleStore
from enterprise.storage.user import User
from enterprise.storage.user_settings import UserSettings

from openhands.storage.data_models.settings import Settings


class UserStore:
    """Store for managing users."""

    @staticmethod
    async def create_user(
        keycloak_user_id: str,
        user_info: dict,
        role_id: Optional[int] = None,
    ) -> User:
        """Create a new user."""
        with session_maker() as session:
            # create personal org
            org = Org(
                name=f'user_{keycloak_user_id}_org',
                contact_name=user_info['preferred_username'],
                contact_email=user_info['email'],
            )
            session.add(org)
            session.flush()  # Flush to get the generated org.id

            settings = await UserStore.create_default_settings(
                org_id=str(org.id), keycloak_user_id=keycloak_user_id
            )

            org_kwargs = OrgStore.get_kwargs_from_settings(settings)
            for key, value in org_kwargs.items():
                if hasattr(org, key):
                    setattr(org, key, value)

            user_kwargs = UserStore.get_kwargs_from_settings(settings)
            user = User(
                keycloak_user_id=keycloak_user_id,
                current_org_id=org.id,
                role_id=role_id,
                **user_kwargs,
            )
            session.add(user)
            session.flush()  # Flush to get the generated user.id

            role = RoleStore.get_role_by_name('admin')

            org_user = OrgUser(
                org_id=org.id,
                user_id=user.id,
                role_id=role.id,  # admin of your own org.
                llm_api_key=settings.llm_api_key,  # type: ignore[union-attr]
                status='active',
            )
            session.add(org_user)
            session.commit()
            session.refresh(user)
            user.org_users  # load org_users
            return user

    @staticmethod
    async def migrate_user(
        keycloak_user_id: str,
        user_settings: UserSettings,
        user_info: dict,
    ) -> User:
        if not keycloak_user_id or not user_settings:
            return None
        kwargs = decrypt_model(
            [
                'llm_api_key',
                'llm_api_key_for_byor',
                'search_api_key',
                'sandbox_api_key',
            ],
            user_settings,
        )
        decrypted_user_settings = UserSettings(**kwargs)
        with session_maker() as session:
            # create personal org
            org = Org(
                name=f'user_{keycloak_user_id}_org',
                contact_name=user_info['preferred_username'],
                contact_email=user_info['email'],
            )
            session.add(org)
            session.flush()  # Flush to get the generated org.id

            await LiteLlmManager.migrate_entries(
                str(org.id), keycloak_user_id, decrypted_user_settings
            )

            await migrate_customer(session, keycloak_user_id, org)

            org_kwargs = {
                c.name: getattr(decrypted_user_settings, c.name)
                for c in Org.__table__.columns
                if c.name != 'id' and hasattr(decrypted_user_settings, c.name)
            }
            for key, value in org_kwargs.items():
                if hasattr(org, key):
                    setattr(org, key, value)

            user_kwargs = {
                c.name: getattr(decrypted_user_settings, c.name)
                for c in User.__table__.columns
                if c.name != 'id' and hasattr(decrypted_user_settings, c.name)
            }
            user = User(
                current_org_id=org.id,
                role_id=None,
                **user_kwargs,
            )
            session.add(user)
            session.flush()  # Flush to get the generated user.id

            role = RoleStore.get_role_by_name('admin')

            org_user = OrgUser(
                org_id=org.id,
                user_id=user.id,
                role_id=role.id,  # admin of your own org.
                llm_api_key=decrypted_user_settings.llm_api_key,  # type: ignore[union-attr]
                status='active',
            )
            session.add(org_user)
            session.delete(user_settings)
            session.commit()
            session.refresh(user)
            user.org_users  # load org_users
            return user

    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[User]:
        """Get user by ID."""
        with session_maker() as session:
            return (
                session.query(User)
                .options(joinedload(User.org_users))
                .filter(User.id == user_id)
                .first()
            )

    @staticmethod
    def get_user_by_keycloak_id(keycloak_user_id: str) -> Optional[User]:
        """Get user by Keycloak user ID."""
        with session_maker() as session:
            return (
                session.query(User)
                .options(joinedload(User.org_users))
                .filter(User.keycloak_user_id == keycloak_user_id)
                .first()
            )

    @staticmethod
    def list_users() -> list[User]:
        """List all users."""
        with session_maker() as session:
            return session.query(User).all()

    @staticmethod
    def update_user(
        user_id: int,
        current_org_id: int,
        role_id: Optional[int] = None,
        enable_sound_notifications: Optional[bool] = None,
    ) -> Optional[User]:
        """Update user details."""
        with session_maker() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                return None

            user.current_org_id = current_org_id
            if role_id is not None:
                user.role_id = role_id
            if enable_sound_notifications is not None:
                user.enable_sound_notifications = enable_sound_notifications

            session.commit()
            session.refresh(user)
            return user

    @staticmethod
    async def create_default_settings(
        org_id: str, keycloak_user_id: str
    ) -> Optional[Settings]:
        logger.info(
            'UserStore:create_default_settings:start',
            extra={'org_id': org_id, 'user_id': keycloak_user_id},
        )
        # You must log in before you get default settings
        if not org_id:
            return None

        settings = Settings(language='en', enable_proactive_conversation_starters=True)

        settings = await LiteLlmManager.create_entries(
            org_id, keycloak_user_id, settings
        )
        if settings is None:
            logger.info(
                'UserStore:create_default_settings:litellm_create_failed',
                extra={'org_id': org_id},
            )
            return None

        return settings

    @staticmethod
    def get_kwargs_from_settings(settings: Settings):
        kwargs = {
            c.name: getattr(settings, c.name)
            for c in User.__table__.columns
            if hasattr(settings, c.name)
        }
        return kwargs
