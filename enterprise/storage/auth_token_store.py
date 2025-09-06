from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Awaitable, Callable, Dict

from sqlalchemy import select, update
from sqlalchemy.orm import sessionmaker
from storage.auth_tokens import AuthTokens
from storage.database import a_session_maker

from openhands.core.logger import openhands_logger as logger
from openhands.integrations.service_types import ProviderType


@dataclass
class AuthTokenStore:
    keycloak_user_id: str
    idp: ProviderType
    a_session_maker: sessionmaker

    @property
    def identity_provider_value(self) -> str:
        return self.idp.value

    async def store_tokens(
        self,
        access_token: str,
        refresh_token: str,
        access_token_expires_at: int,
        refresh_token_expires_at: int,
    ) -> None:
        """Store auth tokens in the database.

        Args:
            access_token: The access token to store
            refresh_token: The refresh token to store
            access_token_expires_at: Expiration time for access token (seconds since epoch)
            refresh_token_expires_at: Expiration time for refresh token (seconds since epoch)
        """
        async with self.a_session_maker() as session:
            async with session.begin():  # Explicitly start a transaction
                result = await session.execute(
                    select(AuthTokens).where(
                        AuthTokens.keycloak_user_id == self.keycloak_user_id,
                        AuthTokens.identity_provider == self.identity_provider_value,
                    )
                )
                token_record = result.scalars().first()

                if token_record:
                    token_record.access_token = access_token
                    token_record.refresh_token = refresh_token
                    token_record.access_token_expires_at = access_token_expires_at
                    token_record.refresh_token_expires_at = refresh_token_expires_at
                else:
                    token_record = AuthTokens(
                        keycloak_user_id=self.keycloak_user_id,
                        identity_provider=self.identity_provider_value,
                        access_token=access_token,
                        refresh_token=refresh_token,
                        access_token_expires_at=access_token_expires_at,
                        refresh_token_expires_at=refresh_token_expires_at,
                    )
                    session.add(token_record)

            await session.commit()  # Commit after transaction block

    async def load_tokens(
        self,
        check_expiration_and_refresh: Callable[
            [ProviderType, str, int, int], Awaitable[Dict[str, str | int]]
        ]
        | None = None,
    ) -> Dict[str, str | int] | None:
        """
        Load authentication tokens from the database and refresh them if necessary.

        This method retrieves the current authentication tokens for the user and checks if they have expired.
        It uses the provided `check_expiration_and_refresh` function to determine if the tokens need
        to be refreshed and to refresh the tokens if needed.

        The method ensures that only one refresh operation is performed per refresh token by using a
        row-level lock on the token record.

        The method is designed to handle race conditions where multiple requests might attempt to refresh
        the same token simultaneously, ensuring that only one refresh call occurs per refresh token.

        Args:
            check_expiration_and_refresh (Callable, optional): A function that checks if the tokens have expired
                and attempts to refresh them. It should return a dictionary containing the new access_token, refresh_token,
                and their respective expiration timestamps. If no refresh is needed, it should return `None`.

        Returns:
            Dict[str, str | int] | None:
                A dictionary containing the access_token, refresh_token, access_token_expires_at,
                and refresh_token_expires_at. If no token record is found, returns `None`.
        """
        async with self.a_session_maker() as session:
            async with session.begin():  # Ensures transaction management
                # Lock the row while we check if we need to refresh the tokens.
                # There is a race condition where 2 or more calls can load tokens simultaneously.
                # If it turns out the loaded tokens are expired, then there will be multiple
                # refresh token calls with the same refresh token. Most IDPs only allow one refresh
                # per refresh token. This lock ensure that only one refresh call occurs per refresh token
                result = await session.execute(
                    select(AuthTokens)
                    .filter(
                        AuthTokens.keycloak_user_id == self.keycloak_user_id,
                        AuthTokens.identity_provider == self.identity_provider_value,
                    )
                    .with_for_update()
                )
                token_record = result.scalars().one_or_none()

                if not token_record:
                    return None

                token_refresh = (
                    await check_expiration_and_refresh(
                        self.idp,
                        token_record.refresh_token,
                        token_record.access_token_expires_at,
                        token_record.refresh_token_expires_at,
                    )
                    if check_expiration_and_refresh
                    else None
                )

                if token_refresh:
                    await session.execute(
                        update(AuthTokens)
                        .where(AuthTokens.id == token_record.id)
                        .values(
                            access_token=token_refresh['access_token'],
                            refresh_token=token_refresh['refresh_token'],
                            access_token_expires_at=token_refresh[
                                'access_token_expires_at'
                            ],
                            refresh_token_expires_at=token_refresh[
                                'refresh_token_expires_at'
                            ],
                        )
                    )
                    await session.commit()

                return (
                    token_refresh
                    if token_refresh
                    else {
                        'access_token': token_record.access_token,
                        'refresh_token': token_record.refresh_token,
                        'access_token_expires_at': token_record.access_token_expires_at,
                        'refresh_token_expires_at': token_record.refresh_token_expires_at,
                    }
                )

    async def is_access_token_valid(self) -> bool:
        """Check if the access token is still valid.

        Returns:
            True if the access token exists and is not expired, False otherwise
        """
        tokens = await self.load_tokens()
        if not tokens:
            return False

        access_token_expires_at = tokens['access_token_expires_at']
        current_time = int(time.time())

        # Return True if the token is not expired (with a small buffer)
        return int(access_token_expires_at) > (current_time + 30)

    async def is_refresh_token_valid(self) -> bool:
        """Check if the refresh token is still valid.

        Returns:
            True if the refresh token exists and is not expired, False otherwise
        """
        tokens = await self.load_tokens()
        if not tokens:
            return False

        refresh_token_expires_at = tokens['refresh_token_expires_at']
        current_time = int(time.time())

        # Return True if the token is not expired (with a small buffer)
        return int(refresh_token_expires_at) > (current_time + 30)

    @classmethod
    async def get_instance(
        cls, keycloak_user_id: str, idp: ProviderType
    ) -> AuthTokenStore:
        """Get an instance of the AuthTokenStore.

        Args:
            config: The application configuration
            keycloak_user_id: The Keycloak user ID

        Returns:
            An instance of AuthTokenStore
        """
        logger.debug(f'auth_token_store.get_instance::{keycloak_user_id}')
        if keycloak_user_id:
            keycloak_user_id = str(keycloak_user_id)
        return AuthTokenStore(
            keycloak_user_id=keycloak_user_id, idp=idp, a_session_maker=a_session_maker
        )
