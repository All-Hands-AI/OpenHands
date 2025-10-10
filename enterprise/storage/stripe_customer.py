from sqlalchemy import Column, DateTime, Integer, String, text
from storage.base import Base


class StripeCustomer(Base):  # type: ignore
    """
    Represents a stripe customer. We can't simply use the stripe API for this because:
    "Don’t use search in read-after-write flows where strict consistency is necessary.
    Under normal operating conditions, data is searchable in less than a minute.
    Occasionally, propagation of new or updated data can be up to an hour behind during outages"
    """

    __tablename__ = 'stripe_customers'
    id = Column(Integer, primary_key=True, autoincrement=True)
    keycloak_user_id = Column(String, nullable=False)
    stripe_customer_id = Column(String, nullable=False)
    created_at = Column(
        DateTime, server_default=text('CURRENT_TIMESTAMP'), nullable=False
    )
    updated_at = Column(
        DateTime,
        server_default=text('CURRENT_TIMESTAMP'),
        onupdate=text('CURRENT_TIMESTAMP'),
        nullable=False,
    )
