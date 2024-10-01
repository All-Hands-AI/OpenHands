from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from oh.asyncio.asyncio_conversation_broker import AsyncioConversationBroker
from oh.fastapi.fastapi import add_open_hands_to_fastapi

conversation_broker = AsyncioConversationBroker(Path("workspace"))


@asynccontextmanager
async def _lifespan(app: FastAPI):
    yield
    await conversation_broker.shutdown()


app = FastAPI(lifespan=_lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
add_open_hands_to_fastapi(app, conversation_broker)
