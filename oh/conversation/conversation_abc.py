from __future__ import annotations
from abc import ABC, abstractmethod
from datetime import datetime
from io import IOBase
from pathlib import Path
from typing import Optional, Union
from uuid import UUID

from oh.event import oh_event
from oh.event.detail.event_detail_abc import EventDetailABC
from oh.event.event_filter import EventFilter
from oh.file.download import Download
from oh.file.file_filter import FileFilter
from oh.file.file_info import FileInfo
from oh.file.file_permissions import FilePermissions
from oh.conversation.listener import conversation_listener_abc
from oh.conversation.conversation_status import ConversationStatus
from oh.storage.page import Page
from oh.task import oh_task
from oh.task.runnable import runnable_abc
from oh.task.task_filter import TaskFilter


class ConversationABC(ABC):
    """
    Conversation combing output events, input tasks, and files, allowing interfacing internally with an
    AI Agent. A user can mantain multiple conversations concurrently, or multiple users could potentially
    share a single conversation.
    * Events represent messages from the server to external clients
    * Tasks represent tasks in progress on the server
    * Files serve to store data related to tasks.

    All methods are designed to make no assumptions about the volume of data / requests being handled,
    and are designed to be environment agnostic - the actual conversation may be running locally or
    remotely / in a docker container.
    Given that different operating systems support different permissions models and that the user is
    only really going to be interested in files the agent can access in this context, the permissions
    model for files is limited. Conversation security is not implemented at this level - it is assumed that
    if you have the UUID for a conversation then you are meant to have access. Security should be implemented
    in the level above this (e.g.: FastAPI) level if required.
    """

    id: UUID
    status: ConversationStatus
    message: Optional[str]
    created_at: datetime
    updated_at: datetime

    @abstractmethod
    async def add_listener(
        self, listener: conversation_listener_abc.ConversationListenerABC
    ) -> UUID:
        """Add a listener and return a unique id for it"""

    @abstractmethod
    async def remove_listener(self, listener_id: UUID) -> bool:
        """Remove the listener with the id given"""

    @abstractmethod
    async def trigger_event(self, detail: EventDetailABC) -> oh_event.OhEvent:
        """Trigger the event given"""

    @abstractmethod
    async def get_event(self, event_id: UUID) -> Optional[oh_event.OhEvent]:
        """Get an event with the id given"""

    @abstractmethod
    async def search_events(
        self, filter: Optional[EventFilter] = None, page_id: Optional[str] = None
    ) -> Page[oh_event.OhEvent]:
        """Search events in this conversation"""

    @abstractmethod
    async def count_events(self, filter: Optional[EventFilter] = None) -> int:
        """Count events in this conversation"""

    @abstractmethod
    async def create_task(
        self,
        runnable: runnable_abc.RunnableABC,
        title: Optional[str] = None,
        delay: float = 0,
    ) -> oh_task.OhTask:
        """Create a task and return details of it.  Throw a SesionError if the conversation is not in a ready state. """

    @abstractmethod
    async def run_task(
        self,
        conversation_id: UUID,
        runnable: runnable_abc.RunnableABC,
        title: Optional[str] = None,
        delay: float = 0,
    ):
        """Run the task and return the result. Throw a SesionError if the conversation is not in a ready state. """

    @abstractmethod
    async def cancel_task(self, task_id: UUID) -> bool:
        """Attempt to cancel task with the id given. Return true if the task was cancelled, false otherwise"""

    @abstractmethod
    async def get_task(self, task_id: UUID) -> Optional[oh_task.OhTask]:
        """Get the handle for the task with the id given"""

    @abstractmethod
    async def search_tasks(
        self, filter: TaskFilter, page_id: str
    ) -> Page[oh_task.OhTask]:
        """Get info on running tasks"""

    @abstractmethod
    async def count_tasks(self, filter: TaskFilter) -> int:
        """Get the number of tasks"""

    @abstractmethod
    async def create_dir(self, path: str) -> FileInfo:
        """
        Make the directory at the path given if it does not exist. Return info in the directory.
        Directories have the mime type `application/x-directory`
        """

    @abstractmethod
    async def create_file(self, path: str) -> FileInfo:
        """Update the updated_at on the file at the path given. If no file exists, create an empty file"""

    @abstractmethod
    async def save_file(self, path: str, content: Union[Path, IOBase]) -> FileInfo:
        """Upload a file to the path given. If no file exists, create an empty file. If a file exists, overwrite it."""

    @abstractmethod
    async def delete_file(self, path: str) -> bool:
        """Delete the file at the path given. Return True if the file existed and was deleted"""

    @abstractmethod
    async def load_file(self, path: str) -> Optional[Download]:
        """Get the file at the path given. Directories are not downloadable. Return a download if the file was retrieved."""

    @abstractmethod
    async def get_file_info(self, path: str) -> Optional[FileInfo]:
        """Get info on a file"""

    @abstractmethod
    async def search_file_info(
        self, filter: FileFilter, page_id: Optional[str] = None
    ) -> Page[FileInfo]:
        """Search files available in the conversation"""

    @abstractmethod
    async def count_files(self, filter: FileFilter) -> int:
        """Search files available in the conversation"""
