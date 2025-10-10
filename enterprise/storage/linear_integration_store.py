from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from storage.database import session_maker
from storage.linear_conversation import LinearConversation
from storage.linear_user import LinearUser
from storage.linear_workspace import LinearWorkspace

from openhands.core.logger import openhands_logger as logger


@dataclass
class LinearIntegrationStore:
    async def create_workspace(
        self,
        name: str,
        linear_org_id: str,
        admin_user_id: str,
        encrypted_webhook_secret: str,
        svc_acc_email: str,
        encrypted_svc_acc_api_key: str,
        status: str = 'active',
    ) -> LinearWorkspace:
        """Create a new Linear workspace with encrypted sensitive data."""

        workspace = LinearWorkspace(
            name=name.lower(),
            linear_org_id=linear_org_id,
            admin_user_id=admin_user_id,
            webhook_secret=encrypted_webhook_secret,
            svc_acc_email=svc_acc_email,
            svc_acc_api_key=encrypted_svc_acc_api_key,
            status=status,
        )

        with session_maker() as session:
            session.add(workspace)
            session.commit()
            session.refresh(workspace)

        logger.info(f'[Linear] Created workspace {workspace.name}')
        return workspace

    async def update_workspace(
        self,
        id: int,
        linear_org_id: Optional[str] = None,
        encrypted_webhook_secret: Optional[str] = None,
        svc_acc_email: Optional[str] = None,
        encrypted_svc_acc_api_key: Optional[str] = None,
        status: Optional[str] = None,
    ) -> LinearWorkspace:
        """Update an existing Linear workspace with encrypted sensitive data."""
        with session_maker() as session:
            # Find existing workspace by ID
            workspace = (
                session.query(LinearWorkspace).filter(LinearWorkspace.id == id).first()
            )

            if not workspace:
                raise ValueError(f'Workspace with ID "{id}" not found')

            if linear_org_id is not None:
                workspace.linear_org_id = linear_org_id

            if encrypted_webhook_secret is not None:
                workspace.webhook_secret = encrypted_webhook_secret

            if svc_acc_email is not None:
                workspace.svc_acc_email = svc_acc_email

            if encrypted_svc_acc_api_key is not None:
                workspace.svc_acc_api_key = encrypted_svc_acc_api_key

            if status is not None:
                workspace.status = status

            session.commit()
            session.refresh(workspace)

        logger.info(f'[Linear] Updated workspace {workspace.name}')
        return workspace

    async def create_workspace_link(
        self,
        keycloak_user_id: str,
        linear_user_id: str,
        linear_workspace_id: int,
        status: str = 'active',
    ) -> LinearUser:
        """Create a new Linear workspace link."""
        linear_user = LinearUser(
            keycloak_user_id=keycloak_user_id,
            linear_user_id=linear_user_id,
            linear_workspace_id=linear_workspace_id,
            status=status,
        )

        with session_maker() as session:
            session.add(linear_user)
            session.commit()
            session.refresh(linear_user)

        logger.info(
            f'[Linear] Created user {linear_user.id} for workspace {linear_workspace_id}'
        )
        return linear_user

    async def get_workspace_by_id(self, workspace_id: int) -> Optional[LinearWorkspace]:
        """Retrieve workspace by ID."""
        with session_maker() as session:
            return (
                session.query(LinearWorkspace)
                .filter(LinearWorkspace.id == workspace_id)
                .first()
            )

    async def get_workspace_by_name(
        self, workspace_name: str
    ) -> Optional[LinearWorkspace]:
        """Retrieve workspace by name."""
        with session_maker() as session:
            return (
                session.query(LinearWorkspace)
                .filter(LinearWorkspace.name == workspace_name.lower())
                .first()
            )

    async def get_user_by_active_workspace(
        self, keycloak_user_id: str
    ) -> LinearUser | None:
        """Get Linear user by Keycloak user ID."""
        with session_maker() as session:
            return (
                session.query(LinearUser)
                .filter(
                    LinearUser.keycloak_user_id == keycloak_user_id,
                    LinearUser.status == 'active',
                )
                .first()
            )

    async def get_user_by_keycloak_id_and_workspace(
        self, keycloak_user_id: str, linear_workspace_id: int
    ) -> Optional[LinearUser]:
        """Get Linear user by Keycloak user ID and workspace ID."""
        with session_maker() as session:
            return (
                session.query(LinearUser)
                .filter(
                    LinearUser.keycloak_user_id == keycloak_user_id,
                    LinearUser.linear_workspace_id == linear_workspace_id,
                )
                .first()
            )

    async def get_active_user(
        self, linear_user_id: str, linear_workspace_id: int
    ) -> Optional[LinearUser]:
        """Get Linear user by Keycloak user ID and workspace ID."""
        with session_maker() as session:
            return (
                session.query(LinearUser)
                .filter(
                    LinearUser.linear_user_id == linear_user_id,
                    LinearUser.linear_workspace_id == linear_workspace_id,
                    LinearUser.status == 'active',
                )
                .first()
            )

    async def update_user_integration_status(
        self, keycloak_user_id: str, status: str
    ) -> LinearUser:
        """Update Linear user integration status."""
        with session_maker() as session:
            linear_user = (
                session.query(LinearUser)
                .filter(LinearUser.keycloak_user_id == keycloak_user_id)
                .first()
            )

            if not linear_user:
                raise ValueError(
                    f'Linear user not found for Keycloak ID: {keycloak_user_id}'
                )

            linear_user.status = status
            session.commit()
            session.refresh(linear_user)

            logger.info(f'[Linear] Updated user {keycloak_user_id} status to {status}')
            return linear_user

    async def deactivate_workspace(self, workspace_id: int):
        """Deactivate the workspace and all user links for a given workspace."""
        with session_maker() as session:
            users = (
                session.query(LinearUser)
                .filter(
                    LinearUser.linear_workspace_id == workspace_id,
                    LinearUser.status == 'active',
                )
                .all()
            )

            for user in users:
                user.status = 'inactive'
                session.add(user)

            workspace = (
                session.query(LinearWorkspace)
                .filter(LinearWorkspace.id == workspace_id)
                .first()
            )
            if workspace:
                workspace.status = 'inactive'
                session.add(workspace)

            session.commit()

        logger.info(f'[Jira] Deactivated all user links for workspace {workspace_id}')

    async def create_conversation(
        self, linear_conversation: LinearConversation
    ) -> None:
        """Create a new Linear conversation record."""
        with session_maker() as session:
            session.add(linear_conversation)
            session.commit()

    async def get_user_conversations_by_issue_id(
        self, issue_id: str, linear_user_id: int
    ) -> LinearConversation | None:
        """Get a Linear conversation by issue ID and linear user ID."""
        with session_maker() as session:
            return (
                session.query(LinearConversation)
                .filter(
                    LinearConversation.issue_id == issue_id,
                    LinearConversation.linear_user_id == linear_user_id,
                )
                .first()
            )

    @classmethod
    def get_instance(cls) -> LinearIntegrationStore:
        """Get an instance of the LinearIntegrationStore."""
        return LinearIntegrationStore()
