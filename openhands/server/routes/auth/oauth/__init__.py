from fastapi import APIRouter
from .github import router as github_router
from .google import router as google_router

router = APIRouter(prefix='/oauth')

router.include_router(github_router)
router.include_router(google_router)
