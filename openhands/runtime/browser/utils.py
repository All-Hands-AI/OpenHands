import base64
import io

import html2text
import numpy as np
from PIL import Image


def get_html_text_converter():
    html_text_converter = html2text.HTML2Text()
    # ignore links and images
    html_text_converter.ignore_links = False
    html_text_converter.ignore_images = True
    # use alt text for images
    html_text_converter.images_to_alt = True
    # disable auto text wrapping
    html_text_converter.body_width = 0
    return html_text_converter


def image_to_png_base64_url(
    image: np.ndarray | Image.Image, add_data_prefix: bool = False
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
    image: np.ndarray | Image.Image, add_data_prefix: bool = False
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
