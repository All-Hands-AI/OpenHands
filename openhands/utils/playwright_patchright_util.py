#!/usr/bin/env python3
"""Utility to use patchright as a drop-in replacement for playwright.

This module provides a function to patch all imports of playwright to use patchright instead.
It uses Python's import system to intercept imports of playwright modules and redirect them
to the corresponding patchright modules.

Usage:
    from openhands.utils.playwright_patchright_util import use_patchright
    use_patchright()  # Call this before any imports of browsergym or playwright
"""

import importlib
import importlib.abc
import importlib.machinery
import importlib.util
import logging
import sys
import types
from typing import Optional, Sequence

logger = logging.getLogger(__name__)


class PlaywrightToPatchrightLoader(importlib.abc.Loader):
    """Custom loader that loads a patchright module but presents it as a playwright module."""

    def __init__(
        self, fullname: str, patchright_name: str, original_loader: importlib.abc.Loader
    ):
        self.fullname = fullname
        self.patchright_name = patchright_name
        self.original_loader = original_loader

    def create_module(
        self, spec: importlib.machinery.ModuleSpec
    ) -> Optional[types.ModuleType]:
        """Create a module object for the patchright module."""
        try:
            # Import the patchright module and return it directly
            return importlib.import_module(self.patchright_name)
        except ImportError as e:
            logger.warning(f'Failed to import {self.patchright_name}: {e}')
            return None

    def exec_module(self, module: types.ModuleType) -> None:
        """Execute the module (nothing to do here as we already set up the module)."""
        pass


class PlaywrightToPatchrightFinder(importlib.abc.MetaPathFinder):
    """Custom finder that intercepts imports of playwright modules and redirects them to patchright."""

    def find_spec(
        self,
        fullname: str,
        path: Optional[Sequence[str]] = None,
        target: Optional[types.ModuleType] = None,
    ) -> Optional[importlib.machinery.ModuleSpec]:
        """Find the module spec for the given module name."""
        # Only handle playwright modules
        if not fullname.startswith('playwright'):
            return None

        # Replace playwright prefix with patchright
        patchright_name = 'patchright' + fullname[len('playwright') :]

        try:
            # Try to find the spec for the patchright module
            spec = importlib.util.find_spec(patchright_name)
            if spec is None:
                return None

            # Create a loader that will load the patchright module
            loader = PlaywrightToPatchrightLoader(
                fullname, patchright_name, spec.loader or importlib.abc.Loader()
            )

            # Create a new spec with the original name but using our custom loader
            new_spec = importlib.machinery.ModuleSpec(
                name=fullname,
                loader=loader,
                origin=spec.origin,
                loader_state=spec.loader_state,
                is_package=spec.submodule_search_locations is not None,
            )

            # Set submodule_search_locations if it's a package
            if spec.submodule_search_locations is not None:
                new_spec.submodule_search_locations = spec.submodule_search_locations

            return new_spec
        except (ImportError, AttributeError) as e:
            logger.warning(f'Failed to find spec for {patchright_name}: {e}')
            return None


def use_patchright():
    """Configure the system to use patchright as a drop-in replacement for playwright.

    This function:
    1. Checks if patchright is installed
    2. Removes any existing playwright modules from sys.modules
    3. Installs a meta path finder to redirect imports

    Call this function before importing any modules that use playwright.
    """
    # Check if patchright is installed
    try:
        importlib.import_module('patchright')
    except ImportError:
        logger.error(
            "Patchright is not installed. Please install it with 'pip install patchright'."
        )
        raise ImportError(
            "Patchright is not installed. Please install it with 'pip install patchright'."
        )

    # Remove any existing playwright modules from sys.modules
    playwright_modules = [
        name
        for name in list(sys.modules.keys())
        if name == 'playwright' or name.startswith('playwright.')
    ]
    for name in playwright_modules:
        del sys.modules[name]

    # Install our custom finder at the beginning of sys.meta_path
    for i, finder in enumerate(sys.meta_path):
        if isinstance(finder, PlaywrightToPatchrightFinder):
            # Already installed
            return

    # Add our finder to the beginning of sys.meta_path
    sys.meta_path.insert(0, PlaywrightToPatchrightFinder())

    logger.info('Patchright will be used as a drop-in replacement for playwright.')


if __name__ == '__main__':
    # Configure logging
    logging.basicConfig(level=logging.INFO)

    # Test the utility
    use_patchright()

    # Try importing playwright
    import playwright

    print(f'Imported module: {playwright.__name__}')
    print(f'Module file: {playwright.__file__}')

    # Try importing sync_api
    from playwright.sync_api import sync_playwright

    print(f'sync_playwright function: {sync_playwright}')

    # Use playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto('https://example.com')
        print(f'Page title: {page.title()}')
        browser.close()
