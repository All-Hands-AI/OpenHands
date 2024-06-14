import logging
import os
from typing import Dict

logger = logging.getLogger(__name__)


class LocalRepository:
    def __init__(self, repo_path: str) -> None:
        self._repo_path = repo_path
        self._files: Dict[str, str] = {}  # in-memory cache of file contents

    @property
    def path(self) -> str:
        return self._repo_path

    def get_file(self, rel_file_path: str):
        file = self._files.get(rel_file_path)

        if file is None:
            abs_file_path = os.path.join(self._repo_path, rel_file_path)
            if not os.path.exists(abs_file_path):
                logger.warning(f'File {abs_file_path} does not exist')
                return None
            if not os.path.isfile(abs_file_path):
                logger.warning(f'Path {abs_file_path} is not a file')
                return None

            with open(abs_file_path, 'r') as f:
                file_content = f.read()
                self._files[rel_file_path] = file_content

        return file_content


class GitHubRepository:
    def __init__(self) -> None:
        # TODO:
        pass
