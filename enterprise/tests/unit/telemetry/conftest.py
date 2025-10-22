"""Conftest for telemetry tests."""

from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from storage.base import Base


@pytest.fixture
def engine():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def session_maker(engine):
    """Create a session maker bound to the test engine."""
    return sessionmaker(bind=engine)


@pytest.fixture
def mock_session_maker():
    """Mock session maker for database tests."""
    mock_session = MagicMock()
    mock_session_maker = MagicMock(return_value=mock_session)
    return mock_session_maker


@pytest.fixture
def mock_database_session():
    """Mock database session with expected query results."""
    session = MagicMock()

    # Mock UserSettings queries
    mock_user_query = MagicMock()
    mock_user_query.count.return_value = 5  # Mock total user count
    mock_user_query.filter.return_value.count.return_value = 3  # Mock active users

    # Mock the session.query() chain
    session.query.return_value = mock_user_query

    return session


@pytest.fixture
def sample_user_settings(session_maker):
    """Create sample user settings for testing."""
    from server.constants import CURRENT_USER_SETTINGS_VERSION
    from storage.user_settings import UserSettings

    with session_maker() as session:
        # Create test users
        from datetime import datetime

        users = [
            UserSettings(
                keycloak_user_id='user1',
                user_version=CURRENT_USER_SETTINGS_VERSION,
                user_consents_to_analytics=True,
                accepted_tos=datetime.now(),
            ),
            UserSettings(
                keycloak_user_id='user2',
                user_version=CURRENT_USER_SETTINGS_VERSION,
                user_consents_to_analytics=True,
                accepted_tos=datetime.now(),
            ),
            UserSettings(
                keycloak_user_id='user3',
                user_version=CURRENT_USER_SETTINGS_VERSION,
                user_consents_to_analytics=False,
                accepted_tos=None,  # This user hasn't accepted ToS
            ),
        ]

        for user in users:
            session.add(user)
        session.commit()

        return users


@pytest.fixture
def mock_async_client():
    """Mock async HTTP client for external API calls."""
    client = MagicMock()
    client.__aenter__ = MagicMock(return_value=client)
    client.__aexit__ = MagicMock(return_value=None)
    client.get = MagicMock()
    client.post = MagicMock()
    return client
