from fastapi import APIRouter, Depends

from app.api.deps import require_basic_auth
from app.api.routes import agent, documents, health, history, prompts

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(agent.router, dependencies=[Depends(require_basic_auth)])
api_router.include_router(documents.router, dependencies=[Depends(require_basic_auth)])
api_router.include_router(history.router, dependencies=[Depends(require_basic_auth)])
api_router.include_router(prompts.router, dependencies=[Depends(require_basic_auth)])
