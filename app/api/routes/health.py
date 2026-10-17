from fastapi import APIRouter

from app.core.database import db_manager
from app.core.metrics import GET_HEALTH_STATUS, track_action

router = APIRouter(tags=["Health"])


@router.get("/health")
@track_action(GET_HEALTH_STATUS)
async def health_check():
    db_ok = False
    try:
        async with db_manager.acquire_pg() as conn:
            val = await conn.fetchval("SELECT 1")
            db_ok = val == 1
    except Exception:
        db_ok = False

    return {
        "status": "healthy" if db_ok else "degraded",
        "database": "connected" if db_ok else "disconnected",
    }
