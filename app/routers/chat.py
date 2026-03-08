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

    # 1b. Fetch user profile and inject into composer_data if available
    try:
        user_result = supabase.table("users").select("*").eq("id", 1).single().execute()
        if user_result.data:
            user_profile = user_result.data
            composer_data = dict(saved_state.get("composer_data") or {})
            if not composer_data.get("author_name") and user_profile.get("name"):
                composer_data["author_name"] = user_profile["name"]
            if not composer_data.get("author_bio") and user_profile.get("bio"):
                composer_data["author_bio"] = user_profile["bio"]
            saved_state["composer_data"] = composer_data
    except Exception:
        logger.debug("Could not fetch user profile, continuing without it")

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
                "Head to the Letters tab to review and edit them."
            )
        elif composer_response and not letters_saved:
            # All letters failed — report the error
            errors = getattr(composer_response, "errors", [])
            if errors:
                logger.warning("Composer errors: %s", errors)
            assistant_message = (
                "I tried to generate the query letters but ran into an issue with the AI service. "
                "This can sometimes happen with content filters. Please try again — you can say "
                "'retry' or 'try again' and I'll re-attempt the letter generation."
            )

    # 6. Sync author bio back to users table if it was improved
    final_composer_data = final_state.get("composer_data") or {}
    updated_bio = (final_composer_data.get("author_bio") or "").strip()
    if updated_bio and len(updated_bio) >= 30:
        try:
            supabase.table("users").update({"bio": updated_bio}).eq("id", 1).execute()
            logger.info("Saved improved author bio to users table")
        except Exception:
            logger.debug("Could not save author bio to users table")

    # 7. Persist graph state back to Supabase
    state_to_save = _serialize_state(final_state)
    state_to_save.pop("user_message", None)

    supabase.table("projects").update({"graph_state": state_to_save}).eq(
        "id", payload.project_id
    ).execute()

    # 8. Return response
    return ChatResponse(
        assistant_message=assistant_message,
        letters_saved=letters_saved,
        current_step=final_state.get("next_step", ""),
    )
