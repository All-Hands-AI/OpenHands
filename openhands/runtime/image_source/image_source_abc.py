from abc import ABC, abstractmethod


class ImageSourceABC(ABC):
    """Source for runtime images."""

    @abstractmethod
    async def get_image(self) -> str:
        """Get the name of the image"""
