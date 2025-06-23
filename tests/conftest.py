"""Global test configuration for OpenHands tests."""

import warnings

# Suppress marshmallow deprecation warning from environs (used by daytona)
# This must be done before any imports that might trigger the warning
warnings.filterwarnings(
    'ignore',
    message=r'.*__version_info__.*deprecated.*',
    category=DeprecationWarning,
    module=r'.*environs.*',
)
