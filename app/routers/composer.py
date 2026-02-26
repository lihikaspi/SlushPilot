from fastapi import APIRouter, HTTPException

from app.schemas.composer import ComposerRequest, ComposerResponse, LetterResult
from app.services.composer import (
    build_batched_composer_prompt,
    generate_query_letters_batch,
    load_fewshot_examples,
    render_query_letter,
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
        if not payload.manuscript.personalization_notes:
            warnings.append("personalization_missing")

        results.append(
            LetterResult(
                publisher=publisher.name,
                letter="",
                warnings=warnings,
            )
        )

    try:
        messages = build_batched_composer_prompt(
            manuscript=payload.manuscript,
            publishers=payload.publishers,
            options=payload.options,
            examples=examples,
        )
        batch_sections = generate_query_letters_batch(
            messages=messages,
            manuscript=payload.manuscript,
            publishers=payload.publishers,
            options=payload.options,
        )
        letters_by_publisher = {
            publisher.name: render_query_letter(
                manuscript=payload.manuscript,
                publisher=publisher,
                sections=sections,
                paraphrase_summary=payload.options.paraphrase_summary,
            )
            for publisher, sections in batch_sections
        }
        for entry in results:
            entry.letter = letters_by_publisher.get(entry.publisher, "")
            if not entry.letter:
                entry.status = "error"
                errors.append(f"{entry.publisher}: missing letter in batch response")
    except Exception as exc:
        errors.append(str(exc))
        for entry in results:
            entry.status = "error"

    return ComposerResponse(letters=results, errors=errors)
