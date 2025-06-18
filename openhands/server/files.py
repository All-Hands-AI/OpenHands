from pydantic import (
    BaseModel,
)


class POSTUploadFilesModel(BaseModel):
    """
    Upload files response model
    """

    file_urls: list[str]
    skipped_files: list[str]
