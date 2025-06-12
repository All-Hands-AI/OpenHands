"""Runtime startup initialization for Railway deployments."""

import os
from openhands.core.config import OpenHandsConfig
from openhands.core.logger import openhands_logger as logger
from openhands.runtime.prebuilt_runtime_manager import initialize_prebuilt_runtime


def initialize_runtime_on_startup():
    """Initialize the runtime system on application startup."""
    logger.info("Initializing runtime system...")
    
    # Create default config
    config = OpenHandsConfig()
    
    # Initialize pre-built runtime if available
    runtime_manager = initialize_prebuilt_runtime(config)
    
    if runtime_manager.is_prebuilt:
        logger.info("✅ Pre-built runtime system initialized successfully")
        status = runtime_manager.get_status()
        logger.info(f"Runtime status: {status}")
    else:
        logger.info("Standard runtime initialization (no pre-built runtime detected)")
    
    return runtime_manager


# Initialize on module import for Railway deployment
if os.getenv('RAILWAY_ENVIRONMENT') or os.getenv('LOCAL_RUNTIME_MODE'):
    logger.info("Railway/Local runtime mode detected - initializing runtime system")
    try:
        initialize_runtime_on_startup()
    except Exception as e:
        logger.error(f"Failed to initialize runtime system: {e}")
        # Don't fail the entire application startup
        pass