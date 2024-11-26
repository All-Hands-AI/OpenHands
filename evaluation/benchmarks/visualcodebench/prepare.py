import base64
import os
from io import BytesIO

import pandas as pd
from huggingface_hub import snapshot_download
from PIL import PngImagePlugin
from tqdm import tqdm

from openhands.core.logger import openhands_logger as logger

REPO_DOWNLOAD_DIR = (
    './evaluation/visualcodebench/'  # Directory to store the downloaded repository
)


def download_repository():
    """
    Download the entire repository from Hugging Face Hub.
    This function clones the repository into REPO_DOWNLOAD_DIR.
    """
    repo_id = 'rvmalhot/VisualCodeBench'
    try:
        logger.info(f"Downloading repository '{repo_id}'...")
        snapshot_download(
            repo_id=repo_id,
            local_dir=REPO_DOWNLOAD_DIR,
            repo_type='dataset',
            ignore_patterns=None,  # Download all files
        )
        logger.info(f"Repository downloaded to '{REPO_DOWNLOAD_DIR}'.")
    except Exception as e:
        logger.error(f"Error downloading repository '{repo_id}': {e}")
        raise e


def format_task_dict(example):
    instance_id = example['id']
    prev_remote_path = os.path.join(REPO_DOWNLOAD_DIR, f'data/{instance_id}/prev')
    post_remote_path = os.path.join(REPO_DOWNLOAD_DIR, f'data/{instance_id}/post')

    # Check if 'prev' and 'post' directories exist
    prev_exists = os.path.exists(prev_remote_path)
    post_exists = os.path.exists(post_remote_path)

    if prev_exists and post_exists:
        skip = False
    else:
        skip = True

    task = {
        'instance_id': instance_id,
        'prev_image': example['prev_image'],
        'post_image': example['post_image'],
        'changes': example['changes'],
        'prev_code_files': example['prev_code_files'],
        'post_code_files': example['post_code_files'],
        'skip': skip,
    }

    return task


def prepare_visualcodebench(dataset):
    logger.info('Processing dataset')
    dataset_processed = []
    for example in tqdm(dataset['train']):
        formatted_example = format_task_dict(example)
        if formatted_example['skip']:
            continue
        del formatted_example['skip']
        dataset_processed.append(formatted_example)

    return pd.DataFrame(dataset_processed)


def pil_image_to_base64(image: PngImagePlugin.PngImageFile) -> str:
    """
    Converts a PIL image to a Base64-encoded string.

    Parameters:
    - image (PngImagePlugin.PngImageFile): The PIL image to convert.

    Returns:
    - str: The Base64-encoded string of the image.
    """
    if not isinstance(image, PngImagePlugin.PngImageFile):
        raise ValueError(
            'The provided image is not a PIL.PngImagePlugin.PngImageFile instance.'
        )

    buffered = BytesIO()
    image.save(buffered, format='PNG')
    img_bytes = buffered.getvalue()
    img_base64 = base64.b64encode(img_bytes).decode('utf-8')
    base64_with_prefix = f'data:image/png;base64,{img_base64}'
    return [base64_with_prefix]
