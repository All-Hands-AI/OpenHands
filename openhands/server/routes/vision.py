from __future__ import annotations

import os
import uuid
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse

from openhands.core.config.llm_config import LLMConfig
from openhands.llm.async_llm import AsyncLLM
from openhands.server.dependencies import get_dependencies
from openhands.server.shared import config as app_config, file_store
from openhands.server.user_auth import get_user_settings
from openhands.storage.data_models.settings import Settings


app = APIRouter(prefix='/api/vision', dependencies=get_dependencies())


@app.post('/extract')
async def extract_text(
    request: Request,
    file: UploadFile = File(...),
    settings: Settings | None = Depends(get_user_settings),
) -> JSONResponse:
    # Save uploaded file to media store
    ext = os.path.splitext(file.filename or '')[1] or '.png'
    rel_path = f"uploads/{uuid.uuid4().hex}{ext}"
    data = await file.read()
    file_store.write(rel_path, data)

    # Build absolute URL for LLM vision
    base = str(request.base_url).rstrip('/')
    image_url = f"{base}/api/media/{rel_path}"

    # Prepare LLM with vision-capable model (falls back to current settings)
    base_cfg = app_config.get_llm_config()
    model_name = (settings.llm_model if settings else base_cfg.model) or base_cfg.model
    llm_cfg = LLMConfig(
        **{
            **base_cfg.model_dump(),
            'model': model_name,
            'base_url': (settings.llm_base_url if settings else base_cfg.base_url) or base_cfg.base_url,
            'api_key': (settings.llm_api_key if settings else base_cfg.api_key) or base_cfg.api_key,
            'disable_vision': False,
        }
    )
    llm = AsyncLLM(config=llm_cfg)

    messages: list[dict[str, Any]] = [
        {
            'role': 'user',
            'content': [
                {'type': 'text', 'text': 'Extract plain text from this image. Return only the text.'},
                {'type': 'image_url', 'image_url': {'url': image_url}},
            ],
        }
    ]

    try:
        resp = await llm.async_completion(messages=messages)
        content = resp['choices'][0]['message']['content']
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Vision extraction failed: {e}')

    return JSONResponse({'text': content, 'image_url': image_url})