from dataclasses import dataclass
from pathlib import Path
from oh.file.file_info import FileInfo


@dataclass
class Download:
    file_info: FileInfo
    path: Path
