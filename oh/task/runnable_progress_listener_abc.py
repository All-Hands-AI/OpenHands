from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID


class RunnableProgressListenerABC(ABC):
    """
    Description of a task which requires an update
    """

    @abstractmethod
    async def update_progress(
        self, task_id: UUID, code: Optional[str], progress: Optional[float]
    ):
        """Update the progress of a task"""
