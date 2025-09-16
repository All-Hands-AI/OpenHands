#!/usr/bin/env python3
"""
Test script to verify remote runtime fixes for mswebench images.
"""

import os
import sys
import logging
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from openhands.runtime.builder.remote import RemoteRuntimeBuilder
from openhands.runtime.utils.runtime_build import build_runtime_image
from openhands.utils.http_session import HttpSession

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_remote_build():
    """Test building a runtime image with the mswebench base image."""
    
    # Configuration
    base_image = "mswebench/alibaba_m_fastjson2:pr-2285"
    api_url = os.getenv('OH_RUNTIME_API_URL', 'https://runtime.eval.all-hands.dev')
    api_key = os.getenv('OH_RUNTIME_API_KEY')
    
    if not api_key:
        logger.error("OH_RUNTIME_API_KEY environment variable is required")
        return False
    
    # Set extended timeout for complex builds
    os.environ['OH_REMOTE_BUILD_TIMEOUT'] = str(90 * 60)  # 90 minutes
    
    try:
        # Create remote runtime builder
        session = HttpSession()
        runtime_builder = RemoteRuntimeBuilder(
            api_url=api_url,
            api_key=api_key,
            session=session
        )
        
        logger.info(f"Testing remote build with base image: {base_image}")
        logger.info(f"Using API URL: {api_url}")
        
        # Test if the base image exists
        if runtime_builder.image_exists(base_image):
            logger.info(f"Base image {base_image} exists in remote registry")
        else:
            logger.warning(f"Base image {base_image} not found in remote registry")
        
        # Build the runtime image
        result_image = build_runtime_image(
            base_image=base_image,
            runtime_builder=runtime_builder,
            platform=None,
            extra_deps=None,
            dry_run=False,
            force_rebuild=False
        )
        
        logger.info(f"Successfully built runtime image: {result_image}")
        return True
        
    except Exception as e:
        logger.error(f"Remote build failed: {e}")
        return False

def main():
    """Main function."""
    logger.info("Starting remote runtime test...")
    
    success = test_remote_build()
    
    if success:
        logger.info("✅ Remote runtime test PASSED")
        sys.exit(0)
    else:
        logger.error("❌ Remote runtime test FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()