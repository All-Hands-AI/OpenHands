"""Tests for LLM settings middleware that validates pro user access."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from pydantic import SecretStr
from storage.subscription_access import SubscriptionAccess

from openhands.storage.data_models.settings import Settings


@pytest.fixture
def mock_session():
    """Mock session for database queries."""
    session = MagicMock()
    return session


@pytest.fixture
def mock_settings_store():
    """Mock settings store dependency."""
    store = MagicMock()
    store.load = AsyncMock()
    return store


@pytest.fixture
def non_llm_settings():
    """Settings containing only non-LLM changes."""
    return Settings(
        language='en',
        enable_sound_notifications=True,
        enable_proactive_conversation_starters=False,
        user_consents_to_analytics=True,
        email='test@example.com',
        git_user_name='test_user',
        git_user_email='test@example.com',
    )


@pytest.fixture
def llm_settings():
    """Settings containing LLM changes from defaults."""
    return Settings(
        language='en',
        llm_model='custom-model',
        llm_api_key=SecretStr('sk-custom-key'),
        llm_base_url='https://custom-endpoint.com',
        agent='CustomAgent',
        confirmation_mode=True,
        security_analyzer='invariant',
        max_budget_per_task=50.0,
        enable_default_condenser=False,
        condenser_max_size=200,
    )


@pytest.fixture
def saas_default_settings():
    """Default SaaS settings to compare against."""
    return Settings(
        language='en',
        agent='CodeActAgent',
        enable_proactive_conversation_starters=True,
        enable_default_condenser=True,
        condenser_max_size=120,
        llm_model='litellm_proxy/prod/claude-sonnet-4-20250514',
        confirmation_mode=False,
        security_analyzer='llm',
        # llm_api_key and llm_base_url are auto-provisioned for SaaS users
        # so any custom values for these are considered changes
    )


class TestLLMSettingsMiddleware:
    """Test cases for LLM settings middleware validation."""

    @pytest.mark.asyncio
    async def test_non_pro_user_changing_non_llm_settings_returns_200(
        self, mock_session, non_llm_settings, saas_default_settings
    ):
        """Non-pro users should be able to change non-LLM settings and get 200."""
        # Mock no active subscription (non-pro user)
        mock_session.query.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value.first.return_value = None

        with patch('enterprise.server.middleware.session_maker') as mock_session_maker:
            mock_session_maker.return_value.__enter__.return_value = mock_session

            # This should not raise any exception (successful validation)
            from enterprise.server.middleware import validate_llm_settings_access

            try:
                await validate_llm_settings_access(
                    'test_user_id', non_llm_settings, saas_default_settings
                )
                # If we reach here, test passes (no exception raised)
            except HTTPException:
                pytest.fail('Non-pro user should be able to change non-LLM settings')

    @pytest.mark.asyncio
    async def test_non_pro_user_changing_llm_settings_returns_403(
        self, mock_session, llm_settings, saas_default_settings
    ):
        """Non-pro users should get 403 when trying to change LLM settings."""
        # Mock no active subscription (non-pro user)
        mock_session.query.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value.first.return_value = None

        with patch('enterprise.server.middleware.session_maker') as mock_session_maker:
            mock_session_maker.return_value.__enter__.return_value = mock_session

            # This should raise HTTPException with 403 status
            from enterprise.server.middleware import validate_llm_settings_access

            with pytest.raises(HTTPException) as exc_info:
                await validate_llm_settings_access(
                    'test_user_id', llm_settings, saas_default_settings
                )

            assert exc_info.value.status_code == 403
            assert 'LLM settings can only be modified by pro users' in str(
                exc_info.value.detail
            )

    @pytest.mark.asyncio
    async def test_pro_user_changing_any_settings_returns_200(
        self, mock_session, llm_settings, saas_default_settings
    ):
        """Pro users should be able to change any settings including LLM and get 200."""
        # Mock active subscription (pro user)
        now = datetime.now(UTC)
        active_subscription = SubscriptionAccess(
            id=1,
            status='ACTIVE',
            user_id='test_user_id',
            start_at=now - timedelta(days=1),
            end_at=now + timedelta(days=30),
            stripe_invoice_payment_id='test_payment_id',
            created_at=now - timedelta(days=1),
            updated_at=now - timedelta(days=1),
        )
        mock_session.query.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value.first.return_value = active_subscription

        with patch('enterprise.server.middleware.session_maker') as mock_session_maker:
            mock_session_maker.return_value.__enter__.return_value = mock_session

            # This should not raise any exception (successful validation)
            from enterprise.server.middleware import validate_llm_settings_access

            try:
                await validate_llm_settings_access(
                    'test_user_id', llm_settings, saas_default_settings
                )
                # If we reach here, test passes (no exception raised)
            except HTTPException:
                pytest.fail('Pro user should be able to change LLM settings')

    @pytest.mark.asyncio
    async def test_pro_user_changing_non_llm_settings_returns_200(
        self, mock_session, non_llm_settings, saas_default_settings
    ):
        """Pro users should be able to change non-LLM settings and get 200."""
        # Mock active subscription (pro user)
        now = datetime.now(UTC)
        active_subscription = SubscriptionAccess(
            id=1,
            status='ACTIVE',
            user_id='test_user_id',
            start_at=now - timedelta(days=1),
            end_at=now + timedelta(days=30),
            stripe_invoice_payment_id='test_payment_id',
            created_at=now - timedelta(days=1),
            updated_at=now - timedelta(days=1),
        )
        mock_session.query.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value.first.return_value = active_subscription

        with patch('enterprise.server.middleware.session_maker') as mock_session_maker:
            mock_session_maker.return_value.__enter__.return_value = mock_session

            # This should not raise any exception (successful validation)
            from enterprise.server.middleware import validate_llm_settings_access

            try:
                await validate_llm_settings_access(
                    'test_user_id', non_llm_settings, saas_default_settings
                )
                # If we reach here, test passes (no exception raised)
            except HTTPException:
                pytest.fail('Pro user should be able to change non-LLM settings')

    def test_llm_settings_detection_custom_model(self, saas_default_settings):
        """Test that custom LLM model is detected as LLM change."""
        from enterprise.server.middleware import has_llm_settings_changes

        llm_settings = Settings(llm_model='custom-model')
        assert has_llm_settings_changes(llm_settings, saas_default_settings) is True

    def test_llm_settings_detection_custom_api_key(self, saas_default_settings):
        """Test that custom API key is detected as LLM change."""
        from enterprise.server.middleware import has_llm_settings_changes

        llm_settings = Settings(llm_api_key=SecretStr('custom-key'))
        assert has_llm_settings_changes(llm_settings, saas_default_settings) is True

        # Any API key (even empty) is considered a custom change
        llm_settings = Settings(llm_api_key=SecretStr(''))
        assert has_llm_settings_changes(llm_settings, saas_default_settings) is True

    def test_llm_settings_detection_custom_base_url(self, saas_default_settings):
        """Test that custom base URL is detected as LLM change."""
        from enterprise.server.middleware import has_llm_settings_changes

        llm_settings = Settings(llm_base_url='https://custom.com')
        assert has_llm_settings_changes(llm_settings, saas_default_settings) is True

        # Empty base URL should NOT be considered a change
        llm_settings = Settings(llm_base_url='')
        assert has_llm_settings_changes(llm_settings, saas_default_settings) is False

    def test_llm_settings_detection_custom_agent(self, saas_default_settings):
        """Test that custom agent is detected as LLM change."""
        from enterprise.server.middleware import has_llm_settings_changes

        llm_settings = Settings(agent='CustomAgent')
        assert has_llm_settings_changes(llm_settings, saas_default_settings) is True

    def test_llm_settings_detection_condenser_changes(self, saas_default_settings):
        """Test that condenser setting changes are detected as LLM change."""
        from enterprise.server.middleware import has_llm_settings_changes

        llm_settings = Settings(enable_default_condenser=False)
        assert has_llm_settings_changes(llm_settings, saas_default_settings) is True

        llm_settings = Settings(condenser_max_size=200)
        assert has_llm_settings_changes(llm_settings, saas_default_settings) is True

        # Same values as defaults should NOT be detected as changes
        llm_settings = Settings(enable_default_condenser=True, condenser_max_size=120)
        assert has_llm_settings_changes(llm_settings, saas_default_settings) is False

    def test_non_llm_settings_detection(self, saas_default_settings):
        """Test that non-LLM settings changes are not detected as LLM changes."""
        from enterprise.server.middleware import has_llm_settings_changes

        non_llm_settings = Settings(
            language='es',
            enable_sound_notifications=True,
            user_consents_to_analytics=False,
            email='new@example.com',
        )
        assert (
            has_llm_settings_changes(non_llm_settings, saas_default_settings) is False
        )

    def test_confirmation_mode_detection(self, saas_default_settings):
        """Test that confirmation mode changes are detected properly."""
        from enterprise.server.middleware import has_llm_settings_changes

        # Setting to True should be detected as change (default is False)
        llm_settings = Settings(confirmation_mode=True)
        assert has_llm_settings_changes(llm_settings, saas_default_settings) is True

        # Setting to False should NOT be detected as change (same as default)
        llm_settings = Settings(confirmation_mode=False)
        assert has_llm_settings_changes(llm_settings, saas_default_settings) is False

    def test_security_analyzer_detection(self, saas_default_settings):
        """Test that security analyzer changes are detected properly."""
        from enterprise.server.middleware import has_llm_settings_changes

        # Different analyzer should be detected as change
        llm_settings = Settings(security_analyzer='invariant')
        assert has_llm_settings_changes(llm_settings, saas_default_settings) is True

        # Same analyzer should NOT be detected as change
        llm_settings = Settings(security_analyzer='llm')
        assert has_llm_settings_changes(llm_settings, saas_default_settings) is False

        # Empty string should NOT be detected as change (treated as None)
        llm_settings = Settings(security_analyzer='')
        assert has_llm_settings_changes(llm_settings, saas_default_settings) is False

    def test_model_detection_with_correct_default(self, saas_default_settings):
        """Test model detection with the correct SaaS default model."""
        from enterprise.server.middleware import has_llm_settings_changes

        # Frontend model should be detected as change
        llm_settings = Settings(llm_model='openhands/claude-sonnet-4-20250514')
        assert has_llm_settings_changes(llm_settings, saas_default_settings) is True

        # SaaS default model should NOT be detected as change
        llm_settings = Settings(llm_model='litellm_proxy/prod/claude-sonnet-4-20250514')
        assert has_llm_settings_changes(llm_settings, saas_default_settings) is False

    @pytest.mark.asyncio
    async def test_llm_settings_middleware_class(self, mock_session):
        """Test the LLMSettingsMiddleware class directly."""
        from unittest.mock import AsyncMock, MagicMock

        from enterprise.server.middleware import LLMSettingsMiddleware

        middleware = LLMSettingsMiddleware()

        # Test non-settings request passes through
        mock_request = MagicMock()
        mock_request.method = 'GET'
        mock_request.url.path = '/api/other'
        mock_call_next = AsyncMock(return_value=MagicMock())

        result = await middleware(mock_request, mock_call_next)
        mock_call_next.assert_called_once_with(mock_request)
        assert result is not None
