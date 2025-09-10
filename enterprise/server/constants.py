import os
import re

# Get the host from environment variable
HOST = os.getenv('WEB_HOST', 'app.all-hands.dev').strip()

# Check if this is a feature environment
# Feature environments have a host format like {some-text}.staging.all-hands.dev
# Just staging.all-hands.dev doesn't count as a feature environment
IS_STAGING_ENV = bool(
    re.match(r'^.+\.staging\.all-hands\.dev$', HOST) or HOST == 'staging.all-hands.dev'
)  # Includes the staging deployment + feature deployments
IS_FEATURE_ENV = (
    IS_STAGING_ENV and HOST != 'staging.all-hands.dev'
)  # Does not include the staging deployment
IS_LOCAL_ENV = bool(HOST == 'localhost')

# Deprecated - billing margins are now handled internally in litellm
DEFAULT_BILLING_MARGIN = float(os.environ.get('DEFAULT_BILLING_MARGIN', '1.0'))

# Map of user settings versions to their corresponding default LLM models
# This ensures that CURRENT_USER_SETTINGS_VERSION and LITELLM_DEFAULT_MODEL stay in sync
USER_SETTINGS_VERSION_TO_MODEL = {
    1: 'claude-3-5-sonnet-20241022',
    2: 'claude-3-7-sonnet-20250219',
    3: 'claude-sonnet-4-20250514',
    4: 'claude-sonnet-4-20250514',
}

LITELLM_DEFAULT_MODEL = os.getenv('LITELLM_DEFAULT_MODEL')

# Current user settings version - this should be the latest key in USER_SETTINGS_VERSION_TO_MODEL
CURRENT_USER_SETTINGS_VERSION = max(USER_SETTINGS_VERSION_TO_MODEL.keys())

LITE_LLM_API_URL = os.environ.get(
    'LITE_LLM_API_URL', 'https://llm-proxy.app.all-hands.dev'
)
LITE_LLM_TEAM_ID = os.environ.get('LITE_LLM_TEAM_ID', None)
LITE_LLM_API_KEY = os.environ.get('LITE_LLM_API_KEY', None)
SUBSCRIPTION_PRICE_DATA = {
    'MONTHLY_SUBSCRIPTION': {
        'unit_amount': 2000,
        'currency': 'usd',
        'product_data': {
            'name': 'OpenHands Monthly',
            'tax_code': 'txcd_10000000',
        },
        'tax_behavior': 'exclusive',
        'recurring': {'interval': 'month', 'interval_count': 1},
    },
}

DEFAULT_INITIAL_BUDGET = float(os.environ.get('DEFAULT_INITIAL_BUDGET', '20'))
STRIPE_API_KEY = os.environ.get('STRIPE_API_KEY', None)
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', None)
REQUIRE_PAYMENT = os.environ.get('REQUIRE_PAYMENT', '0') in ('1', 'true')

SLACK_CLIENT_ID = os.environ.get('SLACK_CLIENT_ID', None)
SLACK_CLIENT_SECRET = os.environ.get('SLACK_CLIENT_SECRET', None)
SLACK_SIGNING_SECRET = os.environ.get('SLACK_SIGNING_SECRET', None)
SLACK_WEBHOOKS_ENABLED = os.environ.get('SLACK_WEBHOOKS_ENABLED', '0') in ('1', 'true')

WEB_HOST = os.getenv('WEB_HOST', 'app.all-hands.dev').strip()
PERMITTED_CORS_ORIGINS = [
    host.strip()
    for host in (os.getenv('PERMITTED_CORS_ORIGINS') or f'https://{WEB_HOST}').split(
        ','
    )
]


def build_litellm_proxy_model_path(model_name: str) -> str:
    """
    Build the LiteLLM proxy model path based on environment and model name.

    This utility constructs the full model path for LiteLLM proxy based on:
    - Environment type (staging vs prod)
    - The provided model name

    Args:
        model_name: The base model name (e.g., 'claude-3-7-sonnet-20250219')

    Returns:
        The full LiteLLM proxy model path (e.g., 'litellm_proxy/prod/claude-3-7-sonnet-20250219')
    """

    if 'prod' in model_name or 'litellm' in model_name or 'proxy' in model_name:
        raise ValueError("Only include model name, don't include prefix")

    prefix = 'litellm_proxy/'

    if not IS_STAGING_ENV and not IS_LOCAL_ENV:
        prefix += 'prod/'

    return prefix + model_name


def get_default_litellm_model():
    """
    Construct proxy for litellm model based on user settings and environment type (staging vs prod)
    if not set explicitly
    """
    if LITELLM_DEFAULT_MODEL:
        return LITELLM_DEFAULT_MODEL
    model = USER_SETTINGS_VERSION_TO_MODEL[CURRENT_USER_SETTINGS_VERSION]
    return build_litellm_proxy_model_path(model)
