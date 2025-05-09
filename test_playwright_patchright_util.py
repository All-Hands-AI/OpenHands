#!/usr/bin/env python3
"""
Test script for the playwright_patchright_util module.
"""

import logging
import sys

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import the use_patchright function
from openhands.utils.playwright_patchright_util import use_patchright

# Use patchright as a replacement for playwright
use_patchright()

# Now import playwright
try:
    from playwright.sync_api import sync_playwright
    
    logger.info("Successfully imported sync_playwright")
    
    # Use playwright
    with sync_playwright() as p:
        logger.info("Successfully created sync_playwright instance")
        
        # Launch a browser
        browser = p.chromium.launch(headless=True)
        logger.info("Successfully launched browser")
        
        # Create a new page
        page = browser.new_page()
        logger.info("Successfully created page")
        
        # Navigate to a URL
        page.goto("https://example.com")
        logger.info(f"Successfully navigated to example.com, title: {page.title()}")
        
        # Close the browser
        browser.close()
        logger.info("Successfully closed browser")
    
except ImportError as e:
    logger.error(f"Import failed: {e}")
except Exception as e:
    logger.error(f"Error during execution: {e}", exc_info=True)

# Print all playwright modules in sys.modules
playwright_modules = [name for name in sys.modules.keys() 
                     if name == 'playwright' or name.startswith('playwright.')]
logger.info(f"Playwright modules in sys.modules: {playwright_modules}")

# Print all patchright modules in sys.modules
patchright_modules = [name for name in sys.modules.keys() 
                     if name == 'patchright' or name.startswith('patchright.')]
logger.info(f"Patchright modules in sys.modules: {patchright_modules}")