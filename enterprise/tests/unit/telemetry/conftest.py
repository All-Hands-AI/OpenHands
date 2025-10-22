"""Conftest for telemetry tests."""
import pytest
from unittest.mock import MagicMock

@pytest.fixture
def mock_session_maker():
    """Mock session maker for database tests."""
    mock_session = MagicMock()
    mock_session_maker = MagicMock(return_value=mock_session)
    return mock_session_maker

@pytest.fixture
def mock_database_session():
    """Mock database session."""
    return MagicMock()