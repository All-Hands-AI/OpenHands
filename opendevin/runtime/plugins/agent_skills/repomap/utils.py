"""
Modifications made on June, 2024.
Description of changes: removed redundant methods, attributes, and adapted some classes to be OpenDevin-specific.
"""

import warnings

with warnings.catch_warnings():
    warnings.simplefilter('ignore')
    import litellm
import tempfile

IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp'}


def is_image_file(file_name):
    """
    Check if a file is an image file based on its extension.

    Args:
        file_name (str): The name of the file.
    """
    file_name = str(file_name)  # Convert file_name to string
    return any(file_name.endswith(ext) for ext in IMAGE_EXTENSIONS)


def get_token_count_from_text(model_name, text):
    """
    Get the token count from the given text using the specified model.

    Args:
        model_name (str): The name of the model to use for token counting.
        text (str): The input text.
    """
    return litellm.token_counter(model=model_name, text=text)


def get_model_max_input_tokens(model_name: str):
    model_info = None
    try:
        if not model_name.startswith('openrouter'):
            model_info = litellm.get_model_info(model_name.split(':')[0])
        else:
            model_info = litellm.get_model_info(model_name)
    # noinspection PyBroadException
    except Exception:
        return 4096

    if model_info is not None and 'max_input_tokens' in model_info:
        max_input_tokens = model_info['max_input_tokens']
    else:
        # Max input tokens for gpt3.5, so this is a safe fallback for any potentially viable model
        max_input_tokens = 4096
    return max_input_tokens


class IgnorantTemporaryDirectory:
    def __init__(self):
        self.temp_dir = tempfile.TemporaryDirectory()

    def __enter__(self):
        return self.temp_dir.__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            self.temp_dir.__exit__(exc_type, exc_val, exc_tb)
        except (OSError, PermissionError):
            pass  # Ignore errors (Windows)
