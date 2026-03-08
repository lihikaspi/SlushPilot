import logging
import time

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.graphs.query_letter_graph import QueryLetterState, build_query_letter_graph
from app.schemas.chat import ChatRequest, ChatResponse, LetterSaved
from app.services.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)

router = APIRouter()

_graph = None


def _get_graph():
    global _graph
    if _graph is None:
        _graph = build_query_letter_graph()
    return _graph


def _serialize_state(state: dict) -> dict:
    """Convert all Pydantic models in state to JSON-safe dicts."""
    result = {}
    for key, value in state.items():
        if isinstance(value, BaseModel):
            result[key] = value.model_dump()
        elif isinstance(value, list):
            result[key] = [
                item.model_dump() if isinstance(item, BaseModel) else item
                for item in value
            ]
        else:
            result[key] = value
    return result


@router.post("/api/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest) -> ChatResponse:
    supabase = get_supabase_client()

    # 1. Load project and saved graph state
    result = (
        supabase.table("projects")
        .select("*")
        .eq("id", payload.project_id)
        .single()
        .execute()
    )
    project = result.data
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    saved_state = project.get("graph_state") or {}
    logger.info("Loaded state for project %s: next_step=%s", payload.project_id, saved_state.get("next_step"))

    # 2. Build input state with new user message
    input_state: QueryLetterState = {**saved_state, "user_message": payload.user_message}

    # 3. Run the graph
    try:
        graph = _get_graph()
        t0 = time.time()
        final_state = graph.invoke(input_state)
        elapsed = time.time() - t0
        logger.info("Graph completed in %.1fs, next_step=%s", elapsed, final_state.get("next_step"))
    except Exception as exc:
        logger.exception("Graph execution error for project %s", payload.project_id)
        raise HTTPException(status_code=500, detail=f"Graph execution error: {exc}")

    # 4. Extract assistant message
    assistant_message = final_state.get("assistant_message", "")

    # 5. If letters were generated, save them to query_letters
    letters_saved = []
    composer_response = final_state.get("letters")
    if composer_response and hasattr(composer_response, "letters"):
        for letter_result in composer_response.letters:
            if letter_result.status == "ok" and letter_result.letter:
                insert_result = (
                    supabase.table("query_letters")
                    .insert(
                        {
                            "project_id": payload.project_id,
                            "publisher": letter_result.publisher,
                            "content": letter_result.letter,
                        }
                    )
                    .execute()
                )
                if insert_result.data:
                    letters_saved.append(
                        LetterSaved(
                            publisher=letter_result.publisher,
                            query_letter_id=insert_result.data[0]["id"],
                        )
                    )

        if letters_saved:
            assistant_message = (
                f"I've drafted {len(letters_saved)} query letters for you! "
                "Head to the Query Letters tab to review and edit them."
            )

    # 6. Persist graph state back to Supabase
    state_to_save = _serialize_state(final_state)
    state_to_save.pop("user_message", None)

    supabase.table("projects").update({"graph_state": state_to_save}).eq(
        "id", payload.project_id
    ).execute()

    # 7. Return response
    return ChatResponse(
        assistant_message=assistant_message,
        letters_saved=letters_saved,
        current_step=final_state.get("next_step", ""),
    )
