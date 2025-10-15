from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import stripe
from fastapi import HTTPException, Request, status
from httpx import Response
from server.routes import billing
from server.routes.billing import (
    CreateBillingSessionResponse,
    CreateCheckoutSessionRequest,
    GetCreditsResponse,
    cancel_callback,
    create_checkout_session,
    create_customer_setup_session,
    get_credits,
    has_payment_method,
    success_callback,
)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from starlette.datastructures import URL
from storage.stripe_customer import Base as StripeCustomerBase


@pytest.fixture
def engine():
    engine = create_engine('sqlite:///:memory:')
    StripeCustomerBase.metadata.create_all(engine)
    return engine


@pytest.fixture
def session_maker(engine):
    return sessionmaker(bind=engine)


@pytest.mark.asyncio
async def test_get_credits_lite_llm_error():
    with (
        patch('integrations.stripe_service.STRIPE_API_KEY', 'mock_key'),
        patch(
            'storage.user_store.UserStore.get_user_by_keycloak_id',
            return_value=MagicMock(current_org_id='mock_org_id'),
        ),
        patch(
            'storage.lite_llm_manager.LiteLlmManager.get_user_team_info',
            side_effect=Exception('LiteLLM API Error'),
        ),
    ):
        with pytest.raises(Exception, match='LiteLLM API Error'):
            await get_credits('mock_user')


@pytest.mark.asyncio
async def test_get_credits_success():
    mock_response = Response(
        status_code=200,
        json={
            'user_info': {
                'spend': 25.50,
                'litellm_budget_table': {'max_budget': 100.00},
            }
        },
        request=MagicMock(),
    )
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value.get.return_value = mock_response

    with (
        patch('integrations.stripe_service.STRIPE_API_KEY', 'mock_key'),
        patch('httpx.AsyncClient', return_value=mock_client),
        patch(
            'storage.user_store.UserStore.get_user_by_keycloak_id',
            return_value=MagicMock(current_org_id='mock_org_id'),
        ),
        patch(
            'storage.lite_llm_manager.LiteLlmManager.get_user_team_info',
            return_value={
                'spend': 25.50,
                'litellm_budget_table': {'max_budget': 100.00},
            },
        ),
    ):
        result = await get_credits('mock_user')

        assert isinstance(result, GetCreditsResponse)
        assert result.credits == Decimal('74.50')  # 100.00 - 25.50 = 74.50


@pytest.mark.asyncio
async def test_create_checkout_session_stripe_error(session_maker):
    """Test handling of Stripe API errors."""
    mock_request = Request(
        scope={
            'type': 'http',
        }
    )
    mock_request._base_url = URL('http://test.com/')

    mock_customer = stripe.Customer(
        id='mock-customer', metadata={'user_id': 'mock-user'}
    )
    mock_customer_create = AsyncMock(return_value=mock_customer)
    with (
        pytest.raises(Exception, match='Stripe API Error'),
        patch('stripe.Customer.create_async', mock_customer_create),
        patch(
            'stripe.Customer.search_async', AsyncMock(return_value=MagicMock(data=[]))
        ),
        patch(
            'stripe.checkout.Session.create_async',
            AsyncMock(side_effect=Exception('Stripe API Error')),
        ),
        patch('integrations.stripe_service.session_maker', session_maker),
        patch(
            'server.auth.token_manager.TokenManager.get_user_info_from_user_id',
            AsyncMock(return_value={'email': 'testy@tester.com'}),
        ),
    ):
        await create_checkout_session(
            CreateCheckoutSessionRequest(amount=25), mock_request, 'mock_user'
        )


@pytest.mark.asyncio
async def test_create_checkout_session_success(session_maker):
    """Test successful creation of checkout session."""
    mock_request = Request(scope={'type': 'http'})
    mock_request._base_url = URL('http://test.com/')

    mock_session = MagicMock()
    mock_session.url = 'https://checkout.stripe.com/test-session'
    mock_session.id = 'test_session_id'
    mock_create = AsyncMock(return_value=mock_session)
    mock_create.return_value = mock_session

    mock_customer = stripe.Customer(
        id='mock-customer', metadata={'user_id': 'mock-user'}
    )
    mock_customer_create = AsyncMock(return_value=mock_customer)
    with (
        patch('stripe.Customer.create_async', mock_customer_create),
        patch(
            'stripe.Customer.search_async', AsyncMock(return_value=MagicMock(data=[]))
        ),
        patch('stripe.checkout.Session.create_async', mock_create),
        patch('server.routes.billing.session_maker') as mock_session_maker,
        patch('integrations.stripe_service.session_maker', session_maker),
        patch(
            'server.auth.token_manager.TokenManager.get_user_info_from_user_id',
            AsyncMock(return_value={'email': 'testy@tester.com'}),
        ),
    ):
        mock_db_session = MagicMock()
        mock_session_maker.return_value.__enter__.return_value = mock_db_session

        result = await create_checkout_session(
            CreateCheckoutSessionRequest(amount=25), mock_request, 'mock_user'
        )

        assert isinstance(result, CreateBillingSessionResponse)
        assert result.redirect_url == 'https://checkout.stripe.com/test-session'

        # Verify Stripe session creation parameters
        mock_create.assert_called_once_with(
            customer='mock-customer',
            line_items=[
                {
                    'price_data': {
                        'unit_amount': 2500,
                        'currency': 'usd',
                        'product_data': {
                            'name': 'OpenHands Credits',
                            'tax_code': 'txcd_10000000',
                        },
                        'tax_behavior': 'exclusive',
                    },
                    'quantity': 1,
                }
            ],
            mode='payment',
            payment_method_types=['card'],
            saved_payment_method_options={'payment_method_save': 'enabled'},
            success_url='http://test.com/api/billing/success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url='http://test.com/api/billing/cancel?session_id={CHECKOUT_SESSION_ID}',
        )

        # Verify database session creation
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_success_callback_session_not_found():
    """Test success callback when billing session is not found."""
    mock_request = Request(scope={'type': 'http'})
    mock_request._base_url = URL('http://test.com/')

    with patch('server.routes.billing.session_maker') as mock_session_maker:
        mock_db_session = MagicMock()
        mock_db_session.query.return_value.filter.return_value.filter.return_value.first.return_value = None
        mock_session_maker.return_value.__enter__.return_value = mock_db_session
        with pytest.raises(HTTPException) as exc_info:
            await success_callback('test_session_id', mock_request)
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        mock_db_session.merge.assert_not_called()
        mock_db_session.commit.assert_not_called()


@pytest.mark.asyncio
async def test_success_callback_stripe_incomplete():
    """Test success callback when Stripe session is not complete."""
    mock_request = Request(scope={'type': 'http'})
    mock_request._base_url = URL('http://test.com/')

    mock_billing_session = MagicMock()
    mock_billing_session.status = 'in_progress'
    mock_billing_session.user_id = 'mock_user'

    with (
        patch('server.routes.billing.session_maker') as mock_session_maker,
        patch('stripe.checkout.Session.retrieve') as mock_stripe_retrieve,
    ):
        mock_db_session = MagicMock()
        mock_db_session.query.return_value.filter.return_value.filter.return_value.first.return_value = mock_billing_session
        mock_session_maker.return_value.__enter__.return_value = mock_db_session

        mock_stripe_retrieve.return_value = MagicMock(status='pending')

        with pytest.raises(HTTPException) as exc_info:
            await success_callback('test_session_id', mock_request)
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        mock_db_session.merge.assert_not_called()
        mock_db_session.commit.assert_not_called()


@pytest.mark.asyncio
async def test_success_callback_success():
    """Test successful payment completion and credit update."""
    mock_request = Request(scope={'type': 'http'})
    mock_request._base_url = URL('http://test.com/')

    mock_billing_session = MagicMock()
    mock_billing_session.status = 'in_progress'
    mock_billing_session.user_id = 'mock_user'

    with (
        patch('server.routes.billing.session_maker') as mock_session_maker,
        patch('stripe.checkout.Session.retrieve') as mock_stripe_retrieve,
        patch(
            'storage.user_store.UserStore.get_user_by_keycloak_id',
            return_value=MagicMock(current_org_id='mock_org_id'),
        ),
        patch(
            'storage.lite_llm_manager.LiteLlmManager.get_user_team_info',
            return_value={
                'spend': 25.50,
                'litellm_budget_table': {'max_budget': 100.00},
            },
        ),
        patch(
            'storage.lite_llm_manager.LiteLlmManager.update_user_in_team'
        ) as mock_update_user,
    ):
        mock_db_session = MagicMock()
        mock_db_session.query.return_value.filter.return_value.filter.return_value.first.return_value = mock_billing_session
        mock_session_maker.return_value.__enter__.return_value = mock_db_session

        mock_stripe_retrieve.return_value = MagicMock(
            status='complete', amount_subtotal=2500, customer='mock_customer_id'
        )  # $25.00 in cents

        response = await success_callback('test_session_id', mock_request)

        assert response.status_code == 302
        assert (
            response.headers['location']
            == 'http://test.com/settings/billing?checkout=success'
        )

        # Verify LiteLLM API calls
        mock_update_user.assert_called_once_with(
            'mock_user',
            'mock_org_id',
            125.0,  # 100 + (25.00 from Stripe)
        )

        # Verify database updates
        assert mock_billing_session.status == 'completed'
        assert mock_billing_session.price == 2500
        mock_db_session.merge.assert_called_once()
        mock_db_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_success_callback_lite_llm_error():
    """Test handling of LiteLLM API errors during success callback."""
    mock_request = Request(scope={'type': 'http'})
    mock_request._base_url = URL('http://test.com/')

    mock_billing_session = MagicMock()
    mock_billing_session.status = 'in_progress'
    mock_billing_session.user_id = 'mock_user'

    with (
        patch('server.routes.billing.session_maker') as mock_session_maker,
        patch('stripe.checkout.Session.retrieve') as mock_stripe_retrieve,
        patch(
            'storage.user_store.UserStore.get_user_by_keycloak_id',
            return_value=MagicMock(current_org_id='mock_org_id'),
        ),
        patch(
            'storage.lite_llm_manager.LiteLlmManager.get_user_team_info',
            side_effect=Exception('LiteLLM API Error'),
        ),
    ):
        mock_db_session = MagicMock()
        mock_db_session.query.return_value.filter.return_value.filter.return_value.first.return_value = mock_billing_session
        mock_session_maker.return_value.__enter__.return_value = mock_db_session

        mock_stripe_retrieve.return_value = MagicMock(
            status='complete', amount_subtotal=2500
        )

        with pytest.raises(Exception, match='LiteLLM API Error'):
            await success_callback('test_session_id', mock_request)

        # Verify no database updates occurred
        assert mock_billing_session.status == 'in_progress'
        mock_db_session.merge.assert_not_called()
        mock_db_session.commit.assert_not_called()


@pytest.mark.asyncio
async def test_cancel_callback_session_not_found():
    """Test cancel callback when billing session is not found."""
    mock_request = Request(scope={'type': 'http'})
    mock_request._base_url = URL('http://test.com/')

    with patch('server.routes.billing.session_maker') as mock_session_maker:
        mock_db_session = MagicMock()
        mock_db_session.query.return_value.filter.return_value.filter.return_value.first.return_value = None
        mock_session_maker.return_value.__enter__.return_value = mock_db_session

        response = await cancel_callback('test_session_id', mock_request)
        assert response.status_code == 302
        assert (
            response.headers['location']
            == 'http://test.com/settings/billing?checkout=cancel'
        )

        # Verify no database updates occurred
        mock_db_session.merge.assert_not_called()
        mock_db_session.commit.assert_not_called()


@pytest.mark.asyncio
async def test_cancel_callback_success():
    """Test successful cancellation of billing session."""
    mock_request = Request(scope={'type': 'http'})
    mock_request._base_url = URL('http://test.com/')

    mock_billing_session = MagicMock()
    mock_billing_session.status = 'in_progress'

    with patch('server.routes.billing.session_maker') as mock_session_maker:
        mock_db_session = MagicMock()
        mock_db_session.query.return_value.filter.return_value.filter.return_value.first.return_value = mock_billing_session
        mock_session_maker.return_value.__enter__.return_value = mock_db_session

        response = await cancel_callback('test_session_id', mock_request)

        assert response.status_code == 302
        assert (
            response.headers['location']
            == 'http://test.com/settings/billing?checkout=cancel'
        )

        # Verify database updates
        assert mock_billing_session.status == 'cancelled'
        mock_db_session.merge.assert_called_once()
        mock_db_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_has_payment_method_with_payment_method():
    """Test has_payment_method returns True when user has a payment method."""

    mock_has_payment_method = AsyncMock(return_value=True)
    with patch(
        'integrations.stripe_service.has_payment_method', mock_has_payment_method
    ):
        result = await has_payment_method('mock_user')
        assert result is True
    mock_has_payment_method.assert_called_once_with('mock_user')


@pytest.mark.asyncio
async def test_has_payment_method_without_payment_method():
    """Test has_payment_method returns False when user has no payment method."""
    mock_has_payment_method = AsyncMock(return_value=False)
    with patch(
        'integrations.stripe_service.has_payment_method', mock_has_payment_method
    ):
        mock_has_payment_method.return_value = False
        result = await has_payment_method('mock_user')
        assert result is False
    mock_has_payment_method.assert_called_once_with('mock_user')


@pytest.mark.asyncio
async def test_create_customer_setup_session_success():
    """Test successful creation of customer setup session."""
    mock_request = Request(scope={'type': 'http', 'headers': []})
    mock_request._base_url = URL('http://test.com/')

    mock_customer = 'mock-customer-id'
    mock_session = MagicMock()
    mock_session.url = 'https://checkout.stripe.com/test-session'
    mock_create = AsyncMock(return_value=mock_session)

    with (
        patch(
            'integrations.stripe_service.find_or_create_customer_by_user_id',
            AsyncMock(return_value=mock_customer),
        ),
        patch('stripe.checkout.Session.create_async', mock_create),
    ):
        result = await create_customer_setup_session(mock_request, 'mock_user')

        assert isinstance(result, billing.CreateBillingSessionResponse)
        assert result.redirect_url == 'https://checkout.stripe.com/test-session'

        # Verify Stripe session creation parameters
        mock_create.assert_called_once_with(
            customer=mock_customer,
            mode='setup',
            payment_method_types=['card'],
            success_url='http://test.com/?free_credits=success',
            cancel_url='http://test.com/',
        )
