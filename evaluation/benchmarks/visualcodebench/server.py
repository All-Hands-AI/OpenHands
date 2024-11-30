import http
import os
import socket
import socketserver
import threading
import time
from io import BytesIO

import requests
from PIL import Image, ImageChops
from playwright.sync_api import sync_playwright

from openhands.core.logger import openhands_logger as logger


def get_free_port():
    """Find a free port to run the HTTP server."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]


def start_http_server(tmpdir):
    port = get_free_port()

    class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
        def translate_path(self, path):
            # Serve files from the specified directory instead of the current working directory
            path = super().translate_path(path)
            relative_path = os.path.relpath(path, os.getcwd())
            return os.path.join(tmpdir, relative_path)

    handler = CustomHTTPRequestHandler
    server = socketserver.TCPServer(('', port), handler)
    return server, port


def capture_screenshot(tmpdir):
    server, port = start_http_server(tmpdir)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    time.sleep(10)

    image = None
    try:
        server_url = f'http://localhost:{port}/'

        if not is_server_reachable(server_url):
            raise RuntimeError(f'Server not reachable at {server_url}')

        screenshot_path = os.path.join(tmpdir, 'final_screenshot.png')
        capture_screenshot_playwright(server_url, screenshot_path)
        image = Image.open(screenshot_path)
        image.load()
    finally:
        # Shut down the server and clean up
        server.shutdown()
        server.server_close()

    return image


def is_server_reachable(url):
    """
    Check if the local server is reachable.
    """
    try:
        response = requests.get(url, timeout=5)  # Set a 5-second timeout
        if response.status_code == 200:
            logger.info(f'Server is reachable at {url}')
            return True
        else:
            logger.warning(
                f'Server responded with status code {response.status_code} at {url}'
            )
            return False
    except requests.ConnectionError as e:
        logger.error(f'Failed to connect to server at {url}: {e}')
        return False


def capture_screenshot_playwright(url, screenshot_path):
    """Capture a screenshot of the given URL using Playwright."""
    try:
        with sync_playwright() as p:
            logger.info('Launching browser...')
            browser = p.chromium.launch(timeout=10000)  # 10 seconds for browser launch

            logger.info('Creating a new page...')
            page = browser.new_page()

            logger.info(f'Navigating to URL: {url}')
            try:
                page.goto(url, timeout=60 * 1000)  # Set timeout to 5 seconds
                logger.info('Page navigation completed.')
            except Exception as e:
                logger.warning(f'Page navigation timed out. {e}. Continuing...')

            logger.info('Waiting for network to be idle...')
            try:
                page.wait_for_load_state(
                    'networkidle', timeout=60 * 1000
                )  # Set timeout to 5 seconds
                logger.info('Page load state reached.')
            except Exception as e:
                logger.warning(f'Page load state timed out. {e}. Continuing...')

            logger.info('Capturing screenshot...')
            page.screenshot(
                path=screenshot_path, full_page=True
            )  # Capture full page screenshot

            logger.info(f'Screenshot saved to {screenshot_path}')
            browser.close()
            return True
    except Exception as e:
        logger.error(f'Error capturing screenshot with Playwright: {e}')
        return False


def evaluate(task, screenshot_path):
    """Compare generated screenshot with post_image using CLIP score."""
    try:
        import torch
        from transformers import CLIPModel, CLIPProcessor

        # Load CLIP model and processor
        model = CLIPModel.from_pretrained('openai/clip-vit-base-patch32')
        processor = CLIPProcessor.from_pretrained('openai/clip-vit-base-patch32')

        # Load images
        post_image = Image.open(BytesIO(task['post_image']))
        generated_img = Image.open(screenshot_path)

        # Process images
        inputs = processor(
            images=[post_image, generated_img], return_tensors='pt', padding=True
        )

        # Get image features
        image_features = model.get_image_features(**inputs)

        # Calculate cosine similarity
        similarity = torch.nn.functional.cosine_similarity(
            image_features[0].unsqueeze(0), image_features[1].unsqueeze(0)
        ).item()

        logger.info(f'CLIP similarity score: {similarity}')

        return similarity > 0.95  # Consider it a match if similarity > 95%
    except Exception as e:
        logger.error(f'Error in CLIP evaluation: {e}')
        # Fallback to pixel comparison if CLIP fails
        try:
            post_image = Image.open(BytesIO(task['post_image']))
            generated_img = Image.open(screenshot_path)

            # Compare images directly without converting to bytes
            diff = ImageChops.difference(generated_img, post_image)
            logger.info(
                f"Pixel difference analysis: {'No difference' if not diff.getbbox() else 'Differences found'}"
            )
            return not diff.getbbox()
        except Exception as ex:
            logger.error(f'Error in fallback evaluation: {ex}')
            return False
