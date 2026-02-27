from fastapi import APIRouter, HTTPException

from app.agents.composer import compose_query_letters
from app.schemas.composer import ComposerRequest, ComposerResponse


router = APIRouter()


@router.post("/api/composer/query-letters", response_model=ComposerResponse)
async def compose_query_letters(payload: ComposerRequest) -> ComposerResponse:
    try:
        return compose_query_letters(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
