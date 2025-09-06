import stripe
from server.auth.token_manager import TokenManager
from server.constants import STRIPE_API_KEY
from server.logger import logger
from storage.database import session_maker
from storage.stripe_customer import StripeCustomer

stripe.api_key = STRIPE_API_KEY


async def find_customer_id_by_user_id(user_id: str) -> str | None:
    # First search our own DB...
    with session_maker() as session:
        stripe_customer = (
            session.query(StripeCustomer)
            .filter(StripeCustomer.keycloak_user_id == user_id)
            .first()
        )
        if stripe_customer:
            return stripe_customer.stripe_customer_id

    # If that fails, fallback to stripe
    search_result = await stripe.Customer.search_async(
        query=f"metadata['user_id']:'{user_id}'",
    )
    data = search_result.data
    if not data:
        logger.info('no_customer_for_user_id', extra={'user_id': user_id})
        return None
    return data[0].id  # type: ignore [attr-defined]


async def find_or_create_customer(user_id: str) -> str:
    customer_id = await find_customer_id_by_user_id(user_id)
    if customer_id:
        return customer_id
    logger.info('creating_customer', extra={'user_id': user_id})

    # Get the user info from keycloak
    token_manager = TokenManager()
    user_info = await token_manager.get_user_info_from_user_id(user_id) or {}

    # Create the customer in stripe
    customer = await stripe.Customer.create_async(
        email=str(user_info.get('email', '')),
        metadata={'user_id': user_id},
    )

    # Save the stripe customer in the local db
    with session_maker() as session:
        session.add(
            StripeCustomer(keycloak_user_id=user_id, stripe_customer_id=customer.id)
        )
        session.commit()

    logger.info(
        'created_customer',
        extra={'user_id': user_id, 'stripe_customer_id': customer.id},
    )
    return customer.id


async def has_payment_method(user_id: str) -> bool:
    customer_id = await find_customer_id_by_user_id(user_id)
    if customer_id is None:
        return False
    payment_methods = await stripe.Customer.list_payment_methods_async(
        customer_id,
    )
    logger.info(
        f'has_payment_method:{user_id}:{customer_id}:{bool(payment_methods.data)}'
    )
    return bool(payment_methods.data)
