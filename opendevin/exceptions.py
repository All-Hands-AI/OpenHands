class MaxCharsExceedError(Exception):
    def __init__(self, num_of_chars=None, max_chars_limit=None):
        if num_of_chars is not None and max_chars_limit is not None:
            # FIXME: autopep8 and mypy are fighting each other on this line
            # autopep8: off
            message = f"Number of characters {num_of_chars} exceeds MAX_CHARS limit: {max_chars_limit}"
        else:
            message = 'Number of characters exceeds MAX_CHARS limit'
        super().__init__(message)
