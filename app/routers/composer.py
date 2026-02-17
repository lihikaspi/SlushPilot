from fastapi import APIRouter, HTTPException

from app.schemas.composer import ComposerRequest, ComposerResponse, LetterResult
from app.services.composer import (
    build_composer_prompt,
    generate_query_letter,
    load_fewshot_examples,
)


router = APIRouter()


@router.post("/api/composer/query-letters", response_model=ComposerResponse)
async def compose_query_letters(payload: ComposerRequest) -> ComposerResponse:
    if not payload.publishers:
        raise HTTPException(status_code=400, detail="publishers list cannot be empty")

    errors = []
    results = []
    try:
        examples = load_fewshot_examples()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    for publisher in payload.publishers:
        warnings = []
        if not publisher.comps:
            warnings.append("comps_missing")
        if not payload.manuscript.personalization_notes and not publisher.special_criteria:
            warnings.append("personalization_missing")

        try:
            messages = build_composer_prompt(
                manuscript=payload.manuscript,
                publisher=publisher,
                options=payload.options,
                examples=examples,
            )
            letter = generate_query_letter(
                messages,
                manuscript=payload.manuscript,
                publisher=publisher,
                options=payload.options,
            )
            results.append(
                LetterResult(
                    publisher=publisher.name,
                    letter=letter,
                    warnings=warnings,
                )
            )
        except Exception as exc:
            errors.append(f"{publisher.name}: {exc}")
            results.append(
                LetterResult(
                    publisher=publisher.name,
                    letter="",
                    status="error",
                    warnings=warnings,
                )
            )

    return ComposerResponse(letters=results, errors=errors)
