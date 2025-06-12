"""Pre-built Runtime Manager for Railway deployments.

This module manages pre-built runtime instances to ensure instant availability
when users start conversations.
"""

import json
import os
import subprocess
import threading
import time
from pathlib import Path
from typing import Dict, Optional

from openhands.core.config import OpenHandsConfig
from openhands.core.logger import openhands_logger as logger


class PrebuiltRuntimeManager:
    """Manages pre-built runtime instances for instant availability."""
    
    def __init__(self, config: OpenHandsConfig):
        self.config = config
        self.runtime_config_path = Path('/app/.openhands-runtime/config.json')
        self.is_prebuilt = self._check_prebuilt_status()
        self._warmup_lock = threading.Lock()
        self._warmup_done = False
        
    def _check_prebuilt_status(self) -> bool:
        """Check if runtime is pre-built and ready."""
        if not self.runtime_config_path.exists():
            return False
            
        try:
            with open(self.runtime_config_path, 'r') as f:
                config = json.load(f)
                return config.get('pre_built', False)
        except (json.JSONDecodeError, IOError):
            return False
    
    def get_runtime_info(self) -> Dict[str, any]:
        """Get information about the pre-built runtime."""
        if not self.is_prebuilt:
            return {'status': 'not_prebuilt'}
            
        try:
            with open(self.runtime_config_path, 'r') as f:
                config = json.load(f)
                return {
                    'status': 'ready',
                    'runtime_type': config.get('runtime_type', 'local'),
                    'build_timestamp': config.get('build_timestamp'),
                    'python_path': config.get('python_path'),
                    'workspace_path': config.get('workspace_path'),
                    'dependencies_verified': config.get('dependencies_verified', False)
                }
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error reading runtime config: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def warmup_runtime(self) -> bool:
        """Warm up the runtime for faster startup."""
        if not self.is_prebuilt:
            logger.warning("Runtime is not pre-built, skipping warmup")
            return False
            
        with self._warmup_lock:
            if self._warmup_done:
                logger.debug("Runtime warmup already completed")
                return True
                
            logger.info("Starting runtime warmup...")
            
            try:
                # Pre-import heavy modules
                self._preimport_modules()
                
                # Verify system dependencies
                self._verify_dependencies()
                
                # Pre-create workspace if needed
                self._prepare_workspace()
                
                self._warmup_done = True
                logger.info("Runtime warmup completed successfully")
                return True
                
            except Exception as e:
                logger.error(f"Runtime warmup failed: {e}")
                return False
    
    def _preimport_modules(self):
        """Pre-import commonly used modules to speed up runtime startup."""
        logger.debug("Pre-importing runtime modules...")
        
        import_script = """
import sys
import os
import subprocess
import tempfile
import threading
import httpx
import tenacity
import openhands
from openhands.core.config import OpenHandsConfig
from openhands.core.logger import openhands_logger
from openhands.runtime.impl.local.local_runtime import LocalRuntime
from openhands.events import EventStream
from openhands.runtime.utils import find_available_tcp_port
print("✅ Module pre-import successful")
"""
        
        result = subprocess.run(
            [self.config.sandbox.local_runtime_url.replace('http://', '').split(':')[0] or 'python', '-c', import_script],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"Module pre-import failed: {result.stderr}")
            
        logger.debug("Module pre-import completed")
    
    def _verify_dependencies(self):
        """Verify that all runtime dependencies are available."""
        logger.debug("Verifying runtime dependencies...")
        
        # Run the health check script
        health_check_path = Path('/app/.openhands-runtime/health-check.py')
        if health_check_path.exists():
            result = subprocess.run(
                ['python', str(health_check_path)],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"Dependency verification failed: {result.stderr}")
                
            logger.debug("Dependency verification completed")
        else:
            logger.warning("Health check script not found, skipping dependency verification")
    
    def _prepare_workspace(self):
        """Prepare the workspace directory."""
        workspace_path = Path('/app/workspace')
        workspace_path.mkdir(exist_ok=True)
        
        # Set proper permissions
        os.chmod(workspace_path, 0o755)
        
        logger.debug(f"Workspace prepared at {workspace_path}")
    
    def start_background_warmup(self):
        """Start runtime warmup in a background thread."""
        if not self.is_prebuilt:
            return
            
        def warmup_worker():
            try:
                time.sleep(2)  # Small delay to let the main app start
                self.warmup_runtime()
            except Exception as e:
                logger.error(f"Background warmup failed: {e}")
        
        warmup_thread = threading.Thread(target=warmup_worker, daemon=True)
        warmup_thread.start()
        logger.info("Started background runtime warmup")
    
    def is_ready(self) -> bool:
        """Check if the runtime is ready for immediate use."""
        return self.is_prebuilt and self._warmup_done
    
    def get_status(self) -> Dict[str, any]:
        """Get comprehensive status of the runtime manager."""
        return {
            'prebuilt': self.is_prebuilt,
            'warmup_done': self._warmup_done,
            'ready': self.is_ready(),
            'runtime_info': self.get_runtime_info()
        }


# Global instance for the application
_runtime_manager: Optional[PrebuiltRuntimeManager] = None


def get_runtime_manager(config: OpenHandsConfig) -> PrebuiltRuntimeManager:
    """Get the global runtime manager instance."""
    global _runtime_manager
    if _runtime_manager is None:
        _runtime_manager = PrebuiltRuntimeManager(config)
    return _runtime_manager


def initialize_prebuilt_runtime(config: OpenHandsConfig) -> PrebuiltRuntimeManager:
    """Initialize and start warming up the pre-built runtime."""
    manager = get_runtime_manager(config)
    
    if manager.is_prebuilt:
        logger.info("Pre-built runtime detected, starting background warmup...")
        manager.start_background_warmup()
    else:
        logger.info("No pre-built runtime detected, using standard initialization")
    
    return manager