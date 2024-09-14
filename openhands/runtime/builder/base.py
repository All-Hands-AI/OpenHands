import abc


class RuntimeBuilder(abc.ABC):
    @abc.abstractmethod
    def build(
        self,
        path: str,
        tags: list[str],
    ) -> str:
        """
        Build the runtime image.

        Args:
            path (str): The path to the runtime image's build directory.
            tags (list[str]): The tags to apply to the runtime image (e.g., ["repo:my-repo", "sha:my-sha"]).

        Returns:
            str: The name:tag of the runtime image after build (e.g., "repo:sha").
                This can be different from the tags input if the builder chooses to mutate the tags (e.g., adding a
                registry prefix). This should be used for subsequent use (e.g., `docker run`).

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
