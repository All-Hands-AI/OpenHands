from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Coroutine, Dict, Optional


class JobStatus(str, Enum):
    PENDING = 'PENDING'
    RUNNING = 'RUNNING'
    COMPLETED = 'COMPLETED'
    FAILED = 'FAILED'


@dataclass
class Job:
    id: str
    type: str
    status: JobStatus = JobStatus.PENDING
    progress: float = 0.0
    result: Any | None = None
    error: str | None = None


class JobManager:
    def __init__(self) -> None:
        self._jobs: Dict[str, Job] = {}
        self._lock = asyncio.Lock()

    def create_job(self, job_type: str) -> Job:
        job_id = uuid.uuid4().hex
        job = Job(id=job_id, type=job_type)
        self._jobs[job_id] = job
        return job

    async def run_job(self, job_id: str, coro_factory: Callable[[], Coroutine[Any, Any, Any]]) -> None:
        job = self._jobs[job_id]
        job.status = JobStatus.RUNNING
        try:
            result = await coro_factory()
            job.result = result
            job.status = JobStatus.COMPLETED
            job.progress = 1.0
        except Exception as e:
            job.error = str(e)
            job.status = JobStatus.FAILED

    def get_job(self, job_id: str) -> Optional[Job]:
        return self._jobs.get(job_id)


# Singleton instance
job_manager = JobManager()