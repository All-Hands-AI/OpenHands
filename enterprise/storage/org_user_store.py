"""
Store class for managing organization-user relationships.
"""

from typing import Optional
from uuid import UUID

from openhands.enterprise.storage.database import session_maker
from openhands.enterprise.storage.org_user import OrgUser


class OrgUserStore:
    """Store for managing organization-user relationships."""

    @staticmethod
    def add_user_to_org(
        org_id: UUID,
        user_id: int,
        role_id: int,
        llm_api_key: str,
        status: Optional[str] = None,
    ) -> OrgUser:
        """Add a user to an organization with a specific role."""
        with session_maker() as session:
            org_user = OrgUser(
                org_id=org_id,
                user_id=user_id,
                role_id=role_id,
                llm_api_key=llm_api_key,
                status=status,
            )
            session.add(org_user)
            session.commit()
            session.refresh(org_user)
            return org_user

    @staticmethod
    def get_org_user(org_id: UUID, user_id: int) -> Optional[OrgUser]:
        """Get organization-user relationship."""
        with session_maker() as session:
            return (
                session.query(OrgUser)
                .filter(OrgUser.org_id == org_id, OrgUser.user_id == user_id)
                .first()
            )

    @staticmethod
    def get_user_orgs(user_id: int) -> list[OrgUser]:
        """Get all organizations for a user."""
        with session_maker() as session:
            return session.query(OrgUser).filter(OrgUser.user_id == user_id).all()

    @staticmethod
    def get_org_users(org_id: UUID) -> list[OrgUser]:
        """Get all users in an organization."""
        with session_maker() as session:
            return session.query(OrgUser).filter(OrgUser.org_id == org_id).all()

    @staticmethod
    def update_user_role_in_org(
        org_id: UUID, user_id: int, role_id: int, status: Optional[str] = None
    ) -> Optional[OrgUser]:
        """Update user's role in an organization."""
        with session_maker() as session:
            org_user = (
                session.query(OrgUser)
                .filter(OrgUser.org_id == org_id, OrgUser.user_id == user_id)
                .first()
            )

            if not org_user:
                return None

            org_user.role_id = role_id
            if status is not None:
                org_user.status = status

            session.commit()
            session.refresh(org_user)
            return org_user

    @staticmethod
    def remove_user_from_org(org_id: UUID, user_id: int) -> bool:
        """Remove a user from an organization."""
        with session_maker() as session:
            org_user = (
                session.query(OrgUser)
                .filter(OrgUser.org_id == org_id, OrgUser.user_id == user_id)
                .first()
            )

            if not org_user:
                return False

            session.delete(org_user)
            session.commit()
            return True