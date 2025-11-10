"""OpenHands package."""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("openhands")
except PackageNotFoundError:
    __version__ = "0.0.0"
