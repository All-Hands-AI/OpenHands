from enum import Enum


class BillingSessionType(Enum):
    DIRECT_PAYMENT = 'DIRECT_PAYMENT'
    MONTHLY_SUBSCRIPTION = 'MONTHLY_SUBSCRIPTION'
