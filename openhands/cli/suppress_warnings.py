"""Module to suppress common warnings."""

import warnings

# Suppress pydub warning about ffmpeg/avconv
warnings.filterwarnings(
    'ignore',
    message="Couldn't find ffmpeg or avconv - defaulting to ffmpeg, but may not work",
    category=RuntimeWarning,
)