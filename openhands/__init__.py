# This is a namespace package - extend the path to include installed packages
# (We need to do this to support dependencies openhands-sdk, openhands-tools and openhands-agent-server
# which all have a top level `openhands`` package.)
__path__ = __import__('pkgutil').extend_path(__path__, __name__)

# Import version information for backward compatibility
# Handle the case where openhands.version might not exist in all namespace package paths
try:
    from openhands.version import __version__, get_version
except ImportError:
    # Fallback: define get_version function directly if version module is not available
    import os
    from pathlib import Path

    __package_name__ = 'openhands_ai'

    def get_version():
        # Try getting the version from pyproject.toml
        try:
            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            candidate_paths = [
                Path(root_dir) / 'pyproject.toml',
                Path(root_dir) / 'openhands' / 'pyproject.toml',
            ]
            for file_path in candidate_paths:
                if file_path.is_file():
                    with open(file_path, 'r') as f:
                        for line in f:
                            if line.strip().startswith('version ='):
                                return (
                                    line.split('=', 1)[1].strip().strip('"').strip("'")
                                )
        except FileNotFoundError:
            pass

        try:
            from importlib.metadata import PackageNotFoundError, version

            return version(__package_name__)
        except (ImportError, PackageNotFoundError):
            pass

        try:
            from pkg_resources import (  # type: ignore
                DistributionNotFound,
                get_distribution,
            )

            return get_distribution(__package_name__).version
        except (ImportError, DistributionNotFound):
            pass

        return 'unknown'

    try:
        __version__ = get_version()
    except Exception:
        __version__ = 'unknown'

__all__ = ['__version__', 'get_version']
