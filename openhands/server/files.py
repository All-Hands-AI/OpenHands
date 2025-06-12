from __future__ import annotations

from pydantic import (
    BaseModel,
)


class POSTUploadFilesModel(BaseModel):
    """
    Upload files response model
    """

    uploaded_files: list[str]
    skipped_files: list[dict[str, str]]
