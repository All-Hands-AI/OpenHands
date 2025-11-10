import os

import posthog

from openhands.core.logger import openhands_logger as logger

# Initialize PostHog
posthog.api_key = os.environ.get('POSTHOG_CLIENT_KEY', 'phc_placeholder')
posthog.host = os.environ.get('POSTHOG_HOST', 'https://us.i.posthog.com')

# Log PostHog configuration with masked API key for security
api_key = posthog.api_key
if api_key and len(api_key) > 8:
    masked_key = f'{api_key[:4]}...{api_key[-4:]}'
else:
    masked_key = 'not_set_or_too_short'
logger.info('posthog_configuration', extra={'posthog_api_key_masked': masked_key})

# Global toggle for the experiment manager
ENABLE_EXPERIMENT_MANAGER = (
    os.environ.get('ENABLE_EXPERIMENT_MANAGER', 'false').lower() == 'true'
)

# Get the current experiment type from environment variable
# If None, no experiment is running
EXPERIMENT_LITELLM_DEFAULT_MODEL_EXPERIMENT = os.environ.get(
    'EXPERIMENT_LITELLM_DEFAULT_MODEL_EXPERIMENT', ''
)
# System prompt experiment toggle
EXPERIMENT_SYSTEM_PROMPT_EXPERIMENT = os.environ.get(
    'EXPERIMENT_SYSTEM_PROMPT_EXPERIMENT', ''
)

EXPERIMENT_CLAUDE4_VS_GPT5 = os.environ.get('EXPERIMENT_CLAUDE4_VS_GPT5', '')

EXPERIMENT_CONDENSER_MAX_STEP = os.environ.get('EXPERIMENT_CONDENSER_MAX_STEP', '')

logger.info(
    'experiment_manager:run_conversation_variant_test:experiment_config',
    extra={
        'enable_experiment_manager': ENABLE_EXPERIMENT_MANAGER,
        'experiment_litellm_default_model_experiment': EXPERIMENT_LITELLM_DEFAULT_MODEL_EXPERIMENT,
        'experiment_system_prompt_experiment': EXPERIMENT_SYSTEM_PROMPT_EXPERIMENT,
        'experiment_claude4_vs_gpt5_experiment': EXPERIMENT_CLAUDE4_VS_GPT5,
        'experiment_condenser_max_step': EXPERIMENT_CONDENSER_MAX_STEP,
    },
)
