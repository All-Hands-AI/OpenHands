import os

__package_name__ = 'openhands_ai'


def get_version():
    try:
        from importlib.metadata import PackageNotFoundError, version

        try:
            return version(__package_name__)
        except PackageNotFoundError:
            pass
    except ImportError:
        pass

    try:
        from pkg_resources import DistributionNotFound, get_distribution

        try:
            return get_distribution(__package_name__).version
        except DistributionNotFound:
            pass
    except ImportError:
        pass

    # Try getting the version from pyproject.toml
    try:
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with open(os.path.join(root_dir, 'pyproject.toml'), 'r') as f:
            for line in f:
                if line.startswith('version ='):
                    return line.split('=')[1].strip().strip('"')
    except FileNotFoundError:
        pass

    return 'unknown'


try:
    __version__ = get_version()
except Exception:
    __version__ = 'unknown'
