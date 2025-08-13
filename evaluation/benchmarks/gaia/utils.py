import base64
import io

import numpy as np
from PIL import Image


def image_to_png_base64_url(
    image: np.ndarray | Image.Image, add_data_prefix: bool = True
):
    """Convert a numpy array to a base64 encoded png image url."""
    if isinstance(image, np.ndarray):
        image = Image.fromarray(image)
    if image.mode in ('RGBA', 'LA'):
        image = image.convert('RGB')
    buffered = io.BytesIO()
    image.save(buffered, format='PNG')

    image_base64 = base64.b64encode(buffered.getvalue()).decode()
    return (
        f'data:image/png;base64,{image_base64}'
        if add_data_prefix
        else f'{image_base64}'
    )


def image_to_jpg_base64_url(
    image: np.ndarray | Image.Image, add_data_prefix: bool = True
):
    """Convert a numpy array to a base64 encoded jpeg image url."""
    if isinstance(image, np.ndarray):
        image = Image.fromarray(image)
    if image.mode in ('RGBA', 'LA'):
        image = image.convert('RGB')
    buffered = io.BytesIO()
    image.save(buffered, format='JPEG')

    image_base64 = base64.b64encode(buffered.getvalue()).decode()
    return (
        f'data:image/jpeg;base64,{image_base64}'
        if add_data_prefix
        else f'{image_base64}'
    )
