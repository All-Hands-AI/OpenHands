import abc


class RuntimeBuilder(abc.ABC):
    @abc.abstractmethod
    def build(
        self,
        path: str,
        tags: list[str],
    ) -> bool:
        """
        Build the runtime image.

        Args:
            path (str): The path to the runtime image's build directory.
            tags (list[str]): The tags to apply to the runtime image (e.g., ["repo:my-repo", "sha:my-sha"]).

        Returns:
            bool: Whether the build was successful.

        Raises:
            RuntimeError: If the build failed.
        """
        pass

    @abc.abstractmethod
    def image_exists(self, image_name: str) -> bool:
        """
        Check if the runtime image exists.

        Args:
            image_name (str): The name of the runtime image (e.g., "repo:sha").

        Returns:
            bool: Whether the runtime image exists.
        """
        pass
