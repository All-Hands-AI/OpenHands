"""Utilities for managing warnings in OpenHands."""

import warnings
from contextlib import contextmanager
from typing import Generator


@contextmanager
def suppress_marshmallow_version_info_warning() -> Generator[None, None, None]:
    """
    Context manager to suppress the specific Marshmallow __version_info__ deprecation warning.

    This warning is triggered by the environs library (used by daytona) when it checks
    marshmallow version compatibility using the deprecated __version_info__ attribute.

    The warning message is:
    "The '__version_info__' attribute is deprecated and will be removed in a future version.
    Use feature detection or 'packaging.Version(importlib.metadata.version("marshmallow")).release' instead."

    This is a temporary fix until daytona updates to a newer version of environs
    that doesn't use the deprecated attribute.
    """
    with warnings.catch_warnings():
        warnings.filterwarnings(
            'ignore',
            message=r'.*__version_info__.*deprecated.*',
            category=DeprecationWarning,
            module=r'.*environs.*',
        )
        yield


def suppress_marshmallow_version_info_warning_globally() -> None:
    """
    Globally suppress the specific Marshmallow __version_info__ deprecation warning.

    This function adds a warning filter that will suppress the deprecation warning
    from environs about using marshmallow's __version_info__ attribute.

    This is a temporary fix until daytona updates to a newer version of environs
    that doesn't use the deprecated attribute.
    """
    warnings.filterwarnings(
        'ignore',
        message=r'.*__version_info__.*deprecated.*',
        category=DeprecationWarning,
        module=r'.*environs.*',
    )
