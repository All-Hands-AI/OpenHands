import logging
import uuid
from typing import Optional

from .file_context import FileContext
from .index.code_index import CodeIndex
from .repository import FileRepository
from .types import FileWithSpans

logger = logging.getLogger(__name__)


class Workspace:
    def __init__(
        self,
        file_repo: FileRepository,
        code_index: CodeIndex,
        workspace_id: Optional[str] = None,
        workspace_dir: Optional[str] = None,
    ):
        self._workspace_dir = workspace_dir
        self._workspace_id = workspace_id or str(uuid.uuid4())

        self.code_index = code_index
        self.file_repo = file_repo

        self._file_context = None

    @classmethod
    def from_dirs(
        cls,
        repo_dir: str,
        index_dir: str,
        workspace_dir: Optional[str] = None,
        **kwargs,
    ):
        file_repo = FileRepository(repo_dir)
        code_index = CodeIndex.from_persist_dir(index_dir, file_repo=file_repo)
        workspace = cls(
            file_repo=file_repo,
            code_index=code_index,
            workspace_dir=workspace_dir,
            **kwargs,
        )
        return workspace

    def create_file_context(
        self, files_with_spans: Optional[list[FileWithSpans]] = None
    ):
        file_context = FileContext(self.file_repo)
        if files_with_spans:
            file_context.add_files_with_spans(files_with_spans)
        return file_context

    def get_file(self, file_path, refresh: bool = False):
        return self.file_repo.get_file(file_path, refresh=refresh)

    def save_file(self, file_path: str, updated_content: Optional[str] = None):
        self.file_repo.save_file(file_path, updated_content)

    def save(self):
        self.file_repo.save()
