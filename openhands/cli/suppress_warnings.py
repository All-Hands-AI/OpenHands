"""Module to suppress common warnings in CLI mode."""

import warnings


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

    # Suppress httpx deprecation warnings about content parameter
    warnings.filterwarnings(
        'ignore',
        message=".*Use 'content=<...>' to upload raw bytes/text content.*",
        category=DeprecationWarning,
    )
    
    # Debug: Add a custom warning handler to track when httpx warnings occur
    import sys
    original_showwarning = warnings.showwarning
    
    def debug_warning_handler(message, category, filename, lineno, file=None, line=None):
        if 'content=' in str(message) and 'httpx' in filename:
            print(f"[DEBUG] HTTPX WARNING DETECTED: {message}", file=sys.stderr)
            print(f"[DEBUG] Location: {filename}:{lineno}", file=sys.stderr)
            print(f"[DEBUG] This warning should be suppressed!", file=sys.stderr)
        return original_showwarning(message, category, filename, lineno, file, line)
    
    warnings.showwarning = debug_warning_handler

    # Suppress general deprecation warnings from dependencies during CLI usage
    # This catches the "Call to deprecated method get_events" warning
    warnings.filterwarnings(
        'ignore',
        message='.*Call to deprecated method.*',
        category=DeprecationWarning,
    )

    # Suppress other common dependency warnings that don't affect functionality
    warnings.filterwarnings(
        'ignore',
        message='.*Expected .* fields but got .*',
        category=UserWarning,
    )


# Apply warning suppressions when module is imported
suppress_cli_warnings()
