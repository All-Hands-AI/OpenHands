import hashlib
from pathlib import Path
from typing import Callable, Dict, Optional

import aiofiles  # type: ignore

from openhands.utils.async_utils import wait_all


async def md5s_for_path(
    path: Path,
    filter: Optional[Callable[[Path], bool]] = None,
    hashes: Optional[Dict[Path, bytes]] = None,
) -> Dict[Path, bytes]:
    if hashes is None:
        hashes = {}
    if filter and not filter(path):
        return hashes
    hash = hashlib.md5()
    if path.is_dir():
        await wait_all(md5s_for_path(c, filter, hashes) for c in Path(path).iterdir())
    else:
        async with aiofiles.open(path, mode='rb') as f:
            async for data in f:
                hash.update(data)
    hashes[path] = hash.digest()
    return hashes
