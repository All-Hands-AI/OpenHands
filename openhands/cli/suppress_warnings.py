"""Module to suppress common warnings in CLI mode."""

import warnings

# Apply critical warning suppressions immediately upon import
warnings.filterwarnings('ignore', message='deprecated', category=DeprecationWarning)
warnings.filterwarnings(
    'ignore',
    message=".*Accessing the 'model_fields' attribute on the instance is deprecated.*",
    category=DeprecationWarning,
)
# Suppress all Pydantic deprecation warnings during CLI usage
warnings.filterwarnings('ignore', category=DeprecationWarning, module='pydantic.*')
warnings.filterwarnings(
    'ignore', message='.*Support for class-based.*', category=DeprecationWarning
)


def suppress_cli_warnings():
    """Suppress common warnings that appear during CLI usage."""

    # Suppress pydub warning about ffmpeg/avconv
    warnings.filterwarnings(
        'ignore',
        message="Couldn't find ffmpeg or avconv - defaulting to ffmpeg, but may not work",
        category=RuntimeWarning,
    )

    # Suppress Pydantic serialization warnings
    warnings.filterwarnings(
        'ignore',
        message='.*Pydantic serializer warnings.*',
        category=UserWarning,
    )

    # Suppress specific Pydantic serialization unexpected value warnings
    warnings.filterwarnings(
        'ignore',
        message='.*PydanticSerializationUnexpectedValue.*',
        category=UserWarning,
    )

    # Suppress general deprecation warnings from dependencies during CLI usage
    # This catches the "Call to deprecated method get_events" warning
    warnings.filterwarnings(
        'ignore',
        message='.*Call to deprecated method.*',
        category=DeprecationWarning,
    )

    # Suppress Pydantic deprecation warnings for deprecated config fields
    # These are expected during the transition period and shouldn't be shown to CLI users
    warnings.filterwarnings(
        'ignore',
        message='deprecated',
        category=DeprecationWarning,
    )

    # Suppress Pydantic model_fields deprecation warnings
    warnings.filterwarnings(
        'ignore',
        message=".*Accessing the 'model_fields' attribute on the instance is deprecated.*",
        category=DeprecationWarning,
    )

    # Suppress all Pydantic deprecation warnings
    warnings.filterwarnings(
        'ignore',
        category=DeprecationWarning,
        module='pydantic.*',
    )

    # Suppress other common dependency warnings that don't affect functionality
    warnings.filterwarnings(
        'ignore',
        message='.*Expected .* fields but got .*',
        category=UserWarning,
    )


# Apply warning suppressions when module is imported
suppress_cli_warnings()
