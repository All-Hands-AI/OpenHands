"""
Test that the models are correctly defined.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from enterprise.storage.base import Base
from enterprise.storage.org import Org
from enterprise.storage.org_user import OrgUser
from enterprise.storage.user import User


@pytest.fixture
def engine():
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def session_maker(engine):
    return sessionmaker(bind=engine)


def test_user_model(session_maker):
    """Test that the User model works correctly."""
    with session_maker() as session:
        # Create a test org
        org = Org(name='test_org')
        session.add(org)
        session.flush()

        # Create a test user
        user = User(
            keycloak_user_id='test-user-id', current_org_id=org.id, language='en'
        )
        session.add(user)
        session.flush()

        # Create org_user relationship
        org_user = OrgUser(
            org_id=org.id,
            user_id=user.id,
            role_id=1,
            llm_api_key='test-api-key',
            status='active',
        )
        session.add(org_user)
        session.commit()

        # Query the user
        queried_user = (
            session.query(User).filter(User.keycloak_user_id == 'test-user-id').first()
        )
        assert queried_user is not None
        assert queried_user.language == 'en'

        # Query the org
        queried_org = session.query(Org).filter(Org.id == org.id).first()
        assert queried_org is not None
        assert queried_org.name == 'test_org'

        # Query the org_user relationship
        queried_org_user = (
            session.query(OrgUser)
            .filter(OrgUser.org_id == org.id, OrgUser.user_id == user.id)
            .first()
        )
        assert queried_org_user is not None
        assert queried_org_user.llm_api_key.get_secret_value() == 'test-api-key'
