from fastapi import APIRouter

from openhands.server.routes.auth.login import router as login_router
from openhands.server.routes.auth.register import router as register_router
from openhands.server.routes.auth.profile import router as profile_router

app = APIRouter(prefix='/api/auth')

app.include_router(login_router)
app.include_router(register_router)
app.include_router(profile_router)
