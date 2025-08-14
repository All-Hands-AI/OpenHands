from __future__ import annotations

import base64
import os
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from openhands.server.dependencies import get_dependencies
from openhands.server.services.jobs import job_manager, JobStatus
from openhands.server.shared import file_store


app = APIRouter(prefix='/api', dependencies=get_dependencies())


MEDIA_ROOT = 'generated'


class ImageRequest(BaseModel):
    prompt: str
    size: str | None = None


class VideoRequest(BaseModel):
    prompt: str
    duration: int | None = None


@app.post('/generate-image')
async def generate_image(req: ImageRequest) -> dict[str, str]:
    job = job_manager.create_job('image')

    async def run() -> dict[str, str]:
        # Placeholder: write a simple PNG header or generated content
        # In real integration, call provider API and write returned bytes
        content = base64.b64decode(
            b'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMAASsJTYQAAAAASUVORK5CYII='
        )
        file_name = f"{MEDIA_ROOT}/images/{uuid.uuid4().hex}.png"
        file_store.write(file_name, content)
        return {"path": f"/api/media/{file_name}"}

    # schedule job
    await job_manager.run_job(job.id, run)
    return {"job_id": job.id}


@app.post('/generate-video')
async def generate_video(req: VideoRequest) -> dict[str, str]:
    job = job_manager.create_job('video')

    async def run() -> dict[str, str]:
        # Placeholder: store a small text as a stand-in for video bytes
        content = b'MOCK_VIDEO_CONTENT'
        file_name = f"{MEDIA_ROOT}/videos/{uuid.uuid4().hex}.mp4"
        file_store.write(file_name, content)
        return {"path": f"/api/media/{file_name}"}

    await job_manager.run_job(job.id, run)
    return {"job_id": job.id}


@app.get('/jobs/{job_id}')
async def get_job(job_id: str) -> JSONResponse:
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail='Job not found')
    return JSONResponse(
        {
            'id': job.id,
            'type': job.type,
            'status': job.status,
            'progress': job.progress,
            'result': job.result,
            'error': job.error,
        }
    )


@app.get('/media/{path:path}')
async def serve_media(path: str) -> Any:
    # Serve bytes from file_store local path
    from fastapi.responses import FileResponse

    # file_store is a LocalFileStore; use its get_full_path if available
    try:
        full_root = file_store.get_full_path("")  # type: ignore[attr-defined]
        full_path = os.path.join(full_root, path)
    except Exception:
        # Fallback: assume file_store.root-like behavior
        full_path = os.path.join(path)

    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail='Not found')
    return FileResponse(full_path)