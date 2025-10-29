# billing.py - Handles all billing-related operations including credit management and Stripe integration
import typing
from datetime import UTC, datetime
from decimal import Decimal

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from integrations import stripe_service
from pydantic import BaseModel
from server.constants import (
    STRIPE_API_KEY,
)
from server.logger import logger
from storage.billing_session import BillingSession
from storage.database import session_maker
from storage.lite_llm_manager import LiteLlmManager
from storage.user_store import UserStore

from openhands.server.user_auth import get_user_id

stripe.api_key = STRIPE_API_KEY
billing_router = APIRouter(prefix='/api/billing')


# TODO: Add a new app_mode named "ON_PREM" to support self-hosted customers instead of doing this
# and members should comment out the "validate_saas_environment" function if they are developing and testing locally.
def is_all_hands_saas_environment(request: Request) -> bool:
    """Check if the current domain is an All Hands SaaS environment.

    Args:
        request: FastAPI Request object

    Returns:
        True if the current domain contains "all-hands.dev" or "openhands.dev" postfix
    """
    hostname = request.url.hostname or ''
    return hostname.endswith('all-hands.dev') or hostname.endswith('openhands.dev')


def validate_saas_environment(request: Request) -> None:
    """Validate that the request is coming from an All Hands SaaS environment.

    Args:
        request: FastAPI Request object

    Raises:
        HTTPException: If the request is not from an All Hands SaaS environment
    """
    if not is_all_hands_saas_environment(request):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Checkout sessions are only available for All Hands SaaS environments',
        )


class GetCreditsResponse(BaseModel):
    credits: Decimal | None = None


class CreateCheckoutSessionRequest(BaseModel):
    amount: int


class CreateBillingSessionResponse(BaseModel):
    redirect_url: str


class GetSessionStatusResponse(BaseModel):
    status: str
    customer_email: str


class LiteLlmUserInfo(typing.TypedDict, total=False):
    max_budget: float | None
    spend: float | None


def calculate_credits(user_info: LiteLlmUserInfo) -> float:
    # using `or` after get with default because it could be missing or present as None.
    max_budget = user_info.get('max_budget') or 0.0
    spend = user_info.get('spend') or 0.0
    return max(max_budget - spend, 0.0)


# Endpoint to retrieve user's current credit balance
@billing_router.get('/credits')
async def get_credits(user_id: str = Depends(get_user_id)) -> GetCreditsResponse:
    if not stripe_service.STRIPE_API_KEY:
        return GetCreditsResponse()
    user = UserStore.get_user_by_id(user_id)
    user_team_info = await LiteLlmManager.get_user_team_info(
        user_id, str(user.current_org_id)
    )
    # Update to use calculate_credits
    spend = user_team_info.get('spend', 0)
    max_budget = (user_team_info.get('litellm_budget_table') or {}).get('max_budget', 0)
    credits = max(max_budget - spend, 0)
    return GetCreditsResponse(credits=Decimal('{:.2f}'.format(credits)))


# Endpoint to check if a user has entered a payment method into stripe
@billing_router.post('/has-payment-method')
async def has_payment_method(user_id: str = Depends(get_user_id)) -> bool:
    if not user_id:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)
    return await stripe_service.has_payment_method_by_user_id(user_id)


# Endpoint to create a new setup intent in stripe
@billing_router.post('/create-customer-setup-session')
async def create_customer_setup_session(
    request: Request, user_id: str = Depends(get_user_id)
) -> CreateBillingSessionResponse:
    validate_saas_environment(request)
    customer_info = await stripe_service.find_or_create_customer_by_user_id(user_id)
    checkout_session = await stripe.checkout.Session.create_async(
        customer=customer_info['customer_id'],
        mode='setup',
        payment_method_types=['card'],
        success_url=f'{request.base_url}?free_credits=success',
        cancel_url=f'{request.base_url}',
    )
    return CreateBillingSessionResponse(redirect_url=checkout_session.url)


# Endpoint to create a new Stripe checkout session for credit purchase
@billing_router.post('/create-checkout-session')
async def create_checkout_session(
    body: CreateCheckoutSessionRequest,
    request: Request,
    user_id: str = Depends(get_user_id),
) -> CreateBillingSessionResponse:
    validate_saas_environment(request)

    customer_info = await stripe_service.find_or_create_customer_by_user_id(user_id)
    checkout_session = await stripe.checkout.Session.create_async(
        customer=customer_info['customer_id'],
        line_items=[
            {
                'price_data': {
                    'unit_amount': body.amount * 100,
                    'currency': 'usd',
                    'product_data': {
                        'name': 'OpenHands Credits',
                        'tax_code': 'txcd_10000000',
                    },
                    'tax_behavior': 'exclusive',
                },
                'quantity': 1,
            },
        ],
        mode='payment',
        payment_method_types=['card'],
        saved_payment_method_options={
            'payment_method_save': 'enabled',
        },
        success_url=f'{request.base_url}api/billing/success?session_id={{CHECKOUT_SESSION_ID}}',
        cancel_url=f'{request.base_url}api/billing/cancel?session_id={{CHECKOUT_SESSION_ID}}',
    )
    logger.info(
        'created_stripe_checkout_session',
        extra={
            'stripe_customer_id': customer_info['customer_id'],
            'user_id': user_id,
            'org_id': customer_info['org_id'],
            'amount': body.amount,
            'checkout_session_id': checkout_session.id,
        },
    )
    with session_maker() as session:
        billing_session = BillingSession(
            id=checkout_session.id,
            user_id=user_id,
            org_id=customer_info['org_id'],
            price=body.amount,
            price_code='NA',
        )
        session.add(billing_session)
        session.commit()

    return CreateBillingSessionResponse(redirect_url=checkout_session.url)


# Callback endpoint for successful Stripe payments - updates user credits and billing session status
@billing_router.get('/success')
async def success_callback(session_id: str, request: Request):
    # We can't use the auth cookie because of SameSite=strict
    with session_maker() as session:
        billing_session = (
            session.query(BillingSession)
            .filter(BillingSession.id == session_id)
            .filter(BillingSession.status == 'in_progress')
            .first()
        )

        if billing_session is None:
            # Hopefully this never happens - we get a redirect from stripe where the session does not exist
            logger.error(
                'session_id_not_found', extra={'checkout_session_id': session_id}
            )
            raise HTTPException(status.HTTP_400_BAD_REQUEST)

        stripe_session = stripe.checkout.Session.retrieve(session_id)
        if stripe_session.status != 'complete':
            # Hopefully this never happens - we get a redirect from stripe where the payment is not yet complete
            # (Or somebody tried to manually build the URL)
            logger.error(
                'payment_not_complete',
                extra={
                    'checkout_session_id': session_id,
                    'stripe_customer_id': stripe_session.customer,
                },
            )
            raise HTTPException(status.HTTP_400_BAD_REQUEST)

        user = UserStore.get_user_by_id(billing_session.user_id)
        user_team_info = await LiteLlmManager.get_user_team_info(
            billing_session.user_id, str(user.current_org_id)
        )
        amount_subtotal = stripe_session.amount_subtotal or 0
        add_credits = amount_subtotal / 100
        max_budget = (user_team_info.get('litellm_budget_table') or {}).get(
            'max_budget', 0
        )
        new_max_budget = max_budget + add_credits

        await LiteLlmManager.update_team_and_users_budget(
            str(user.current_org_id), new_max_budget
        )

        # Store transaction status
        billing_session.status = 'completed'
        billing_session.price = add_credits
        billing_session.updated_at = datetime.now(UTC)
        session.merge(billing_session)
        logger.info(
            'stripe_checkout_success',
            extra={
                'amount_subtotal': stripe_session.amount_subtotal,
                'user_id': billing_session.user_id,
                'org_id': str(user.current_org_id),
                'checkout_session_id': billing_session.id,
                'stripe_customer_id': stripe_session.customer,
            },
        )
        session.commit()

    return RedirectResponse(
        f'{request.base_url}settings/billing?checkout=success', status_code=302
    )


# Callback endpoint for cancelled Stripe payments - updates billing session status
@billing_router.get('/cancel')
async def cancel_callback(session_id: str, request: Request):
    with session_maker() as session:
        billing_session = (
            session.query(BillingSession)
            .filter(BillingSession.id == session_id)
            .filter(BillingSession.status == 'in_progress')
            .first()
        )
        if billing_session:
            logger.info(
                'stripe_checkout_cancel',
                extra={
                    'user_id': billing_session.user_id,
                    'checkout_session_id': billing_session.id,
                },
            )
            billing_session.status = 'cancelled'
            billing_session.updated_at = datetime.now(UTC)
            session.merge(billing_session)
            session.commit()

    return RedirectResponse(
        f'{request.base_url}settings/billing?checkout=cancel', status_code=302
    )
