"""
Store class for managing organization-member relationships.
"""

from typing import Optional
from uuid import UUID

from storage.database import session_maker
from storage.org_member import OrgMember


class OrgMemberStore:
    """Store for managing organization-member relationships."""

    @staticmethod
    def add_user_to_org(
        org_id: UUID,
        user_id: UUID,
        role_id: int,
        llm_api_key: str,
        status: Optional[str] = None,
    ) -> OrgMember:
        """Add a user to an organization with a specific role."""
        with session_maker() as session:
            org_member = OrgMember(
                org_id=org_id,
                user_id=user_id,
                role_id=role_id,
                llm_api_key=llm_api_key,
                status=status,
            )
            session.add(org_member)
            session.commit()
            session.refresh(org_member)
            return org_member

    @staticmethod
    def get_org_member(org_id: UUID, user_id: int) -> Optional[OrgMember]:
        """Get organization-user relationship."""
        with session_maker() as session:
            return (
                session.query(OrgMember)
                .filter(OrgMember.org_id == org_id, OrgMember.user_id == user_id)
                .first()
            )

    @staticmethod
    def get_user_orgs(user_id: int) -> list[OrgMember]:
        """Get all organizations for a user."""
        with session_maker() as session:
            return session.query(OrgMember).filter(OrgMember.user_id == user_id).all()

    @staticmethod
    def get_org_members(org_id: UUID) -> list[OrgMember]:
        """Get all users in an organization."""
        with session_maker() as session:
            return session.query(OrgMember).filter(OrgMember.org_id == org_id).all()

    @staticmethod
    def update_user_role_in_org(
        org_id: UUID, user_id: int, role_id: int, status: Optional[str] = None
    ) -> Optional[OrgMember]:
        """Update user's role in an organization."""
        with session_maker() as session:
            org_member = (
                session.query(OrgMember)
                .filter(OrgMember.org_id == org_id, OrgMember.user_id == user_id)
                .first()
            )

            if not org_member:
                return None

            org_member.role_id = role_id
            if status is not None:
                org_member.status = status

            session.commit()
            session.refresh(org_member)
            return org_member

    @staticmethod
    def remove_user_from_org(org_id: UUID, user_id: int) -> bool:
        """Remove a user from an organization."""
        with session_maker() as session:
            org_member = (
                session.query(OrgMember)
                .filter(OrgMember.org_id == org_id, OrgMember.user_id == user_id)
                .first()
            )

            if not org_member:
                return False

            session.delete(org_member)
            session.commit()
            return True
