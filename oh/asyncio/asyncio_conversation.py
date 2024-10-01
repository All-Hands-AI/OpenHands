import asyncio
import base64
from dataclasses import dataclass, field
from datetime import datetime
import glob
from io import IOBase
from itertools import count
import itertools
import logging
import mimetypes
import os
from pathlib import Path, PurePosixPath
import shutil
from typing import Dict, List, Optional, Union
from uuid import UUID, uuid4

from oh.event.detail.event_detail_abc import EventDetailABC
from oh.event.event_filter import EventFilter
from oh.event.oh_event import OhEvent
from oh.asyncio.asyncio_progress_listener import AsyncioProgressListener
from oh.file.download import Download
from oh.file.file_error import FileError
from oh.file.file_filter import FileFilter
from oh.file.file_info import FileInfo
from oh.file.file_permissions import FilePermissions
from oh.conversation.listener.conversation_listener_abc import ConversationListenerABC
from oh.conversation.conversation_abc import ConversationABC
from oh.conversation.conversation_error import ConversationError
from oh.conversation.conversation_status import ConversationStatus
from oh.storage.mem_storage import MemStorage
from oh.storage.page import Page
from oh.storage.storage_abc import StorageABC
from oh.task.oh_task import OhTask
from oh.task.runnable.runnable_abc import RunnableABC
from oh.task.task_filter import TaskFilter
from oh.task.task_status import TaskStatus
from oh.util.sync_to_async import sync_to_async

_aio_copy = sync_to_async(shutil.copy)
_aio_copyfileobj = sync_to_async(shutil.copyfileobj)
_aio_rmtree = sync_to_async(shutil.rmtree)
_LOGGER = logging.getLogger(__name__)


@dataclass
class AsyncioConversation(ConversationABC):
    workspace_path: Path
    id: UUID = field(default_factory=uuid4)
    status: ConversationStatus = ConversationStatus.CREATING
    message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    listeners: Dict[UUID, ConversationListenerABC] = field(default_factory=dict)
    event_storage: StorageABC[OhEvent, EventFilter] = field(default_factory=MemStorage)
    task_storage: StorageABC[OhTask, TaskFilter] = field(default_factory=MemStorage)
    asyncio_tasks: Dict[UUID, asyncio.Task] = field(default_factory=dict)
    max_file_page_size: int = 100

    def __post_init__(self):
        self.workspace_path = self.workspace_path.absolute()

    async def add_listener(self, listener: ConversationListenerABC) -> UUID:
        listener_id = uuid4()
        self.listeners[listener_id] = listener
        return listener_id

    async def remove_listener(self, listener_id: UUID) -> bool:
        return self.listeners.pop(listener_id) is not None

    async def trigger_event(self, detail: EventDetailABC):
        event = OhEvent(conversation_id=self.id, detail=detail)
        await self.event_storage.create(event)
        _LOGGER.debug(f'conversation_event:{self.id}:{event}')
        if self.listeners:
            await asyncio.wait(
                [
                    asyncio.create_task(listener.on_event(event))
                    for listener in self.listeners.values()
                ]
            )

    async def get_event(self, event_id: UUID) -> Optional[OhEvent]:
        return await self.event_storage.read(event_id)

    async def search_events(
        self, filter: Optional[EventFilter] = None, page_id: Optional[str] = None
    ) -> Page[OhEvent]:
        return await self.event_storage.search(filter, page_id)

    async def count_events(self, filter: Optional[EventFilter] = None) -> int:
        return await self.event_storage.count(filter)

    async def create_task(
        self, runnable: RunnableABC, title: Optional[str] = None, delay: float = 0
    ) -> OhTask:
        if self.status != ConversationStatus.READY:
            raise ConversationError(str(self.status))
        task = OhTask(
            conversation_id=self.id,
            runnable=runnable,
            title=title,
            status=TaskStatus.PENDING if delay else TaskStatus.RUNNING,
        )
        await self.task_storage.create(task)
        asyncio_task = asyncio.create_task(self._run_task(task, delay))
        self.asyncio_tasks[task.id] = asyncio_task
        return task

    async def run_task(
        self,
        conversation_id: UUID,
        runnable: RunnableABC,
        title: Optional[str] = None,
        delay: float = 0,
    ):
        if self.status != ConversationStatus.READY:
            raise ConversationError(str(self.status))
        task = await self.create_task(conversation_id, runnable, title, delay)
        result = await self.asyncio_tasks[task.id]
        return result

    async def cancel_task(self, task_id: UUID) -> bool:
        task = await self.task_storage.read(task_id)
        if (
            task is None
            or task.status not in [TaskStatus.PENDING, TaskStatus.RUNNING]
            or not task.runnable.cancellable
        ):
            return False
        asyncio_task = self.asyncio_tasks.get(task.id)
        if asyncio_task is None:
            return False
        task.status = TaskStatus.CANCELLING
        self.task_storage.update(task)
        await self.asyncio_tasks[task.id]
        return True

    async def get_task(self, task_id: UUID) -> Optional[OhTask]:
        return await self.task_storage.read(task_id)

    async def search_tasks(
        self, filter: Optional[TaskFilter] = None, page_id: Optional[str] = None
    ) -> Page[OhTask]:
        return await self.task_storage.search(filter, page_id)

    async def count_tasks(self, filter: TaskFilter) -> int:
        return await self.task_storage.count(filter)

    async def _run_task(self, task: OhTask, delay: float):
        try:
            if delay:
                await asyncio.sleep(delay)
            await task.runnable.run(
                task_id=task.id,
                progress_listener=AsyncioProgressListener(
                    task.id, self.task_storage, self
                ),
                conversation=self,
            )
        finally:
            self.asyncio_tasks.pop(task.id)

    def _to_internal_path(self, path: str) -> Path:
        result = Path(self.workspace_path, PurePosixPath(path)).resolve()
        if not result.startswith(self.workspace_path):
            raise FileError(f"invalid_path:{path}")
        return result

    def _to_file_info(self, path: Path) -> FileInfo:
        external_path = str(
            PurePosixPath(*path.parts[len(self.workspace_path.parts) :])
        )
        if path.is_dir():
            external_path += "/"  # Directories end with a trailing slash.
        mime_type = (
            "application/x-directory" if path.is_dir() else mimetypes.guess_type(path)
        )
        return FileInfo(
            path=external_path,
            size_in_bytes=os.path.getsize(path),
            updated_at=datetime.fromtimestamp(os.path.getmtime(path)),
            permissions=FilePermissions(
                os.access(path, os.R_OK),
                os.access(path, os.W_OK),
                os.access(path, os.X_OK),
            ),
            mime_type=mime_type[0],
        )

    async def create_dir(self, path: str) -> FileInfo:
        internal_path = self._to_internal_path(path)
        if internal_path.exists():
            if not internal_path.is_dir():
                raise FileError("not_a_directory:{path}")
        else:
            internal_path.mkdir(parents=True, exist_ok=True)
        return self._to_file_info(internal_path)

    async def create_file(self, path: str) -> FileInfo:
        internal_path = self._to_internal_path(path)
        if internal_path.exists():
            if internal_path.is_dir():
                raise FileError("not_a_file:{path}")
        else:
            internal_path.parent.mkdir(parents=True, exist_ok=True)
            open(internal_path, "w").close()
        return self._to_file_info(internal_path)

    async def save_file(self, path: str, content: Union[Path, IOBase]) -> FileInfo:
        internal_path = self._to_internal_path(path)
        internal_path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, Path):
            await _aio_copy(content, internal_path)
        else:
            with open(internal_path, "wb") as destination:
                await _aio_copyfileobj(content, destination)

    async def delete_file(self, path: str) -> bool:
        internal_path = self._to_internal_path(path)
        if not internal_path.exists():
            return False
        await _aio_rmtree(internal_path)
        return True

    async def load_file(self, path: str) -> Optional[Download]:
        internal_path = self._to_internal_path(path)
        if not internal_path.exists() or not os.access(internal_path, os.R_OK):
            return False
        return Download(file_info=self._to_file_info, path=path)

    async def get_file_info(self, path: str) -> Optional[FileInfo]:
        internal_path = self._to_internal_path(path)
        if not internal_path.exists():
            return None
        return self._to_file_info(internal_path)

    async def search_file_info(
        self, filter: FileFilter, page_id: Optional[str] = None
    ) -> Page[FileInfo]:
        paths = iter(await self._list_files(filter))

        # For this purpose we simply incode an offset in base64. We encode it to insulate against
        # folks thinking that a number is a part of the spec - the page key may not be a number
        # in other impls!
        skip = 0
        if page_id:
            skip = int(base64.b64decode(page_id))
        sum(1 for _ in itertools.islice(paths, skip))

        results = list(
            self._to_file_info(path)
            for path in itertools.islice(paths, self.max_file_page_size)
        )

        # Check if there are  more results...
        next_page_id = None
        try:
            next(paths)
            next_page_id = base64.b64encode(str(skip + self.max_file_page_size))
        except StopIteration:
            next_page_id = None

        return Page(results, next_page_id)

    async def count_files(self, filter: Optional[FileFilter]) -> int:
        return count(self._list_files(filter))

    async def _list_files(self, filter: Optional[FileFilter]) -> List[Path]:
        list_path = await self._get_list_path(filter)
        if filter and filter.path_delimiter == "/":
            files = os.listdir(list_path)
            paths = [Path(list_path, file) for file in files]
            return paths
        files = glob(Path(list_path, "**", "*"))
        paths = [Path(file) for file in files]
        return paths

    async def _get_list_path(self, filter: Optional[FileFilter]) -> Path:
        if filter and filter.path_prefix:
            return self._to_internal_path(filter.path_prefix)
        return self.workspace_path

    async def destroy(self, grace_period: int):
        _LOGGER.info(f"destroying_conversation:{self.id}")
        self.status = ConversationStatus.DESTROYING
        try:
            await self._graceful_shutdown(grace_period)
        except TimeoutError:
            # A non graceful shutdown - we may have to cancel tasks in progress
            _LOGGER.info(f"cancelling_all_tasks:{self.id}")
            for task in self.asyncio_tasks:
                task.cancel()
        _LOGGER.info(f"conversation_destroyed:{self.id}")
    
    async def _graceful_shutdown(self, grace_period: int):
        page_id = None
        while True:
            page = await self.search_tasks(page_id=page_id)
            for task in page.results:
                if task.status not in [TaskStatus.PENDING, TaskStatus.RUNNING] or not task.runnable.cancellable:
                    continue
                task.status = TaskStatus.CANCELLING
                asyncio.create_task(self.task_storage.update(task))

            if page.next_page_id:
                page_id = page.next_page_id
            else:
                await asyncio.wait(self.asyncio_tasks.values(), timeout=grace_period)
