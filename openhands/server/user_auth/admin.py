
from functools import wraps
from inspect import signature, Parameter
from typing import Callable

from fastapi import Depends, HTTPException

from openhands.server.user_auth import get_user_settings
from openhands.storage.data_models.settings import Settings


def get_admin_user_settings(user_settings: Settings = Depends(get_user_settings)) -> Settings:
    """ Method designed for use as a dependency.
    Currently uses `get_uset_settings` dependency, but could use `get_user_id` or `get_user_auth`
    """
    # This is a mock value - your code will use a role check
    if not user_settings.email_verified:
        raise HTTPException(status_code=400, detail='insufficient_access')

    return user_settings


def requires_admin(fn: Callable):
    """ Decorator for endpoints indicating admin is required - should be applied after the fastapi decorator. """

    @wraps(fn)
    def wrapper(*args, **kwargs):
        # Pop the dependency off the wrapped function which, does not use it.
        kwargs.pop('user_settings')
        result = fn(*args, **kwargs)
        return result

    # Update the signature of the returned function to include the dependency so that FastAPI knows to inject it.
    sig = signature(wrapper)
    parameters = list(sig.parameters.values())
    parameters.append(
        Parameter(
            name='user_settings',
            kind=Parameter.KEYWORD_ONLY,
            annotation=Settings,
            default=Depends(get_admin_user_settings),
        )
    )
    sig = sig.replace(parameters=parameters)
    wrapper.__signature__ = sig  # type: ignore

    return wrapper
