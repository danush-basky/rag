from fastapi import APIRouter, Query

from app.core.metrics import GET_SESSION_HISTORY, GET_SESSION_SUMMARY, track_action
from app.models.schemas import ChatMessageReadDB, SessionSummaryDB
from app.services.history import history_service

router = APIRouter(prefix="/history", tags=["History"])


@router.get("/{session_id}", response_model=list[ChatMessageReadDB])
@track_action(GET_SESSION_HISTORY)
async def get_session_history(
    session_id: str,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    return await history_service.get_history(session_id, limit=limit, offset=offset)


@router.get("/{session_id}/summary", response_model=SessionSummaryDB | None)
@track_action(GET_SESSION_SUMMARY)
async def get_session_summary(session_id: str):
    return await history_service.get_summary(session_id)
