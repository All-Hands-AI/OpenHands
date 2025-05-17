import io
import base64
from PIL import Image
import numpy as np

def image_to_png_base64_url(
    image: np.ndarray | Image.Image,
    add_data_prefix: bool = False,
    max_size_kb: int = 1024,
    minimum_quality: int = 10,
) -> str:
    """Convert a numpy array to a base64 encoded png image url.
    
    Will not guarantee the size of the image, but will attempt to compress it to below the specified maximum size.

    Args:
        image: The image to convert.
        add_data_prefix: Whether to add the data prefix to the base64 string.
        max_size_kb: Maximum size of the image in kilobytes.
        minimum_quality: Minimum quality of the image.
    """
    if isinstance(image, np.ndarray):
        image = Image.fromarray(image)
    if image.mode in ('RGBA', 'LA'):
        image = image.convert('RGB')

    max_size_bytes = max_size_kb * 1024
    quality = 85

    while True:
        buffered = io.BytesIO()
        image.save(buffered, format='PNG', quality=quality)

        if len(buffered.getvalue()) <= max_size_bytes:
            break

        # If the buffer is too large, reduce the quality.
        quality -= 5
        if quality < minimum_quality:
            break

    image_base64 = base64.b64encode(buffered.getvalue()).decode()
    return (
        f'data:image/png;base64,{image_base64}'
        if add_data_prefix
        else f'{image_base64}'
    )

def png_base64_url_to_image(png_base64_url: str) -> Image.Image:
    """Convert a base64 encoded png image url to a PIL Image."""
    splited = png_base64_url.split(',')
    if len(splited) == 2:
        base64_data = splited[1]
    else:
        base64_data = png_base64_url
    return Image.open(io.BytesIO(base64.b64decode(base64_data)))
