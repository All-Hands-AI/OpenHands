from __future__ import annotations

import asyncio
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from openhands.server.dependencies import get_dependencies
from openhands.server.shared import config as app_config

app = APIRouter(prefix='/api/runtime', dependencies=get_dependencies())


@app.post('/prepull')
async def prepull_images() -> dict[str, Any]:
  try:
    import docker  # local import to avoid import issues if docker not installed
  except Exception as e:
    raise HTTPException(status_code=500, detail=f'Docker SDK not available: {e}')

  base = app_config.sandbox.base_container_image
  runtime = app_config.sandbox.runtime_container_image

  if not base and not runtime:
    return {"ok": True, "message": "No images configured"}

  client = docker.from_env()
  pulled: list[str] = []
  errors: list[str] = []

  def _pull(img: str) -> None:
    try:
      if img:
        client.images.pull(img)
        pulled.append(img)
    except Exception as ex:
      errors.append(f'{img}: {ex}')

  loop = asyncio.get_running_loop()
  tasks = []
  if base:
    tasks.append(loop.run_in_executor(None, _pull, base))
  if runtime and runtime != base:
    tasks.append(loop.run_in_executor(None, _pull, runtime))
  if tasks:
    await asyncio.gather(*tasks)

  client.close()
  return {"ok": len(errors) == 0, "pulled": pulled, "errors": errors}