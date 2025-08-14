from __future__ import annotations

import asyncio
from typing import Any, AsyncIterator

from fastapi import APIRouter, Request
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from openhands.core.config.llm_config import LLMConfig
from openhands.core.config import load_openhands_config
from openhands.server.dependencies import get_dependencies


app = APIRouter(prefix='/api', dependencies=get_dependencies())


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    model: str | None = None
    stream: bool = True


async def _stream_completion(
    llm, messages: list[dict[str, Any]]
) -> AsyncIterator[str]:
    async for chunk in llm.async_streaming_completion(messages=messages):
        try:
            delta = chunk['choices'][0]['delta'].get('content', '')
        except Exception:
            delta = ''
        if delta:
            yield delta
        await asyncio.sleep(0)  # cooperative multitasking


@app.post('/chat')
async def chat_sse(
    req: ChatRequest,
    request: Request,
) -> EventSourceResponse:
    # Import lazily to avoid circular imports during module load
    from openhands.llm.streaming_llm import StreamingLLM  # noqa: WPS433

    # Get base config
    base_cfg = load_openhands_config().get_llm_config()

    # Try to obtain user settings dynamically (optional)
    settings_model = None
    try:
        from openhands.server.user_auth import get_user_settings  # type: ignore
        settings_model = await get_user_settings(request)  # type: ignore
    except Exception:
        settings_model = None

    if settings_model is not None:
        llm_config = LLMConfig(
            **{
                **base_cfg.model_dump(),
                'model': (req.model or settings_model.llm_model or base_cfg.model),
                'base_url': settings_model.llm_base_url or base_cfg.base_url,
                'api_key': settings_model.llm_api_key or base_cfg.api_key,
            }
        )
    else:
        llm_config = base_cfg

    llm = StreamingLLM(config=llm_config)

    # Convert ChatMessage -> dict for litellm
    msgs: list[dict[str, Any]] = [m.model_dump() for m in req.messages]

    async def event_gen() -> AsyncIterator[dict[str, str]]:
        yield {"event": "start", "data": ""}
        async for token in _stream_completion(llm, msgs):
            yield {"event": "message", "data": token}
        yield {"event": "end", "data": ""}

    return EventSourceResponse(event_gen(), media_type='text/event-stream')