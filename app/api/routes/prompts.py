from fastapi import APIRouter, HTTPException

from app.models.schemas import PromptsResponse, PromptsUpdate
from app.services.prompts import prompt_store

router = APIRouter(prefix="/prompts", tags=["Prompts"])


def _current() -> PromptsResponse:
    return PromptsResponse(
        system_prompt=prompt_store.system_prompt,
        context_prompt=prompt_store.context_prompt,
    )


@router.get("", response_model=PromptsResponse)
async def get_prompts() -> PromptsResponse:
    return _current()


@router.put("", response_model=PromptsResponse)
async def set_prompts(body: PromptsUpdate) -> PromptsResponse:
    if body.system_prompt is None and body.context_prompt is None:
        raise HTTPException(
            status_code=400,
            detail="Provide system_prompt, context_prompt, or both.",
        )
    try:
        prompt_store.update(
            system_prompt=body.system_prompt,
            context_prompt=body.context_prompt,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _current()
