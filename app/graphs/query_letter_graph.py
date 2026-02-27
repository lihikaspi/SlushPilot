import os
from pathlib import Path
from typing import Any, Dict, List, Optional, TypedDict

try:
    from langgraph.graph import END, StateGraph
except ImportError:  # pragma: no cover - optional dependency
    END = None
    StateGraph = None

from app.agents.composer import compose_query_letters
from app.agents.strategist import (
    StrategistManuscript,
    create_strategist_service,
    execute_strategist_pipeline,
)
import config
from app.agents.clarify import generate_clarification
from app.agents.intake import parse_intake
from app.schemas.composer import (
    ComposerOptions,
    ComposerRequest,
    ComposerResponse,
    Manuscript,
    Publisher,
)


class QueryLetterState(TypedDict, total=False):
    user_message: str
    assistant_message: str
    strategist_data: Dict[str, Any]
    composer_data: Dict[str, Any]
    strategist_input: StrategistManuscript
    composer_input: Manuscript
    publishers: List[Publisher]
    letters: Optional[ComposerResponse]
    missing_fields: List[str]
    errors: List[str]
    next_step: str


def _missing_strategist_fields(strategist_data: Dict[str, Any]) -> List[str]:
    if not strategist_data:
        return [
            "strategist.title",
            "strategist.genre",
            "strategist.word_count",
            "strategist.blurb",
            "strategist.comparative_titles",
            "strategist.target_audience",
        ]

    missing = []
    title = (strategist_data.get("title") or "").strip()
    genre = (strategist_data.get("genre") or "").strip()
    word_count = strategist_data.get("word_count") or 0
    blurb = (strategist_data.get("blurb") or "").strip()
    comps = strategist_data.get("comparative_titles") or []
    target_audience = (strategist_data.get("target_audience") or "").strip()

    if not title:
        missing.append("strategist.title")
    if not genre:
        missing.append("strategist.genre")
    if word_count <= 0:
        missing.append("strategist.word_count")
    if not blurb:
        missing.append("strategist.blurb")
    if not comps:
        missing.append("strategist.comparative_titles")
    if not target_audience:
        missing.append("strategist.target_audience")
    return missing


def _missing_composer_fields(composer_data: Dict[str, Any]) -> List[str]:
    if not composer_data:
        return [
            "composer.title",
            "composer.word_count",
            "composer.genre",
            "composer.summary",
            "composer.author_name",
        ]

    missing = []
    title = (composer_data.get("title") or "").strip()
    genre = (composer_data.get("genre") or "").strip()
    word_count = composer_data.get("word_count") or 0
    summary = (composer_data.get("summary") or "").strip()
    author_name = (composer_data.get("author_name") or "").strip()

    if not title:
        missing.append("composer.title")
    if word_count <= 0:
        missing.append("composer.word_count")
    if not genre:
        missing.append("composer.genre")
    if not summary:
        missing.append("composer.summary")
    if not author_name:
        missing.append("composer.author_name")
    return missing


def _strategist_ready() -> List[str]:
    errors = []
    if not config.OPENAI_API_KEY:
        errors.append("Missing OPENAI_API_KEY")
    if not config.PINECONE_API_KEY:
        errors.append("Missing PINECONE_API_KEY")
    if not Path(config.STRATEGIST_BM25_PATH).exists():
        errors.append(f"Missing BM25 weights: {config.STRATEGIST_BM25_PATH}")
    return errors


def _supervisor_node(state: QueryLetterState) -> dict:
    errors = _strategist_ready()
    if errors:
        return {"errors": errors, "next_step": "end"}

    if state.get("user_message"):
        return {"next_step": "intake"}

    strategist_data = state.get("strategist_data") or {}
    composer_data = state.get("composer_data") or {}

    if os.getenv("DEBUG_INTAKE") == "1":
        print("Supervisor strategist_data:", strategist_data)
        print("Supervisor composer_data:", composer_data)

    missing_fields = _missing_strategist_fields(strategist_data)
    if os.getenv("DEBUG_INTAKE") == "1":
        print("Supervisor missing strategist fields:", missing_fields)
    if missing_fields:
        return {"missing_fields": missing_fields, "next_step": "clarify"}

    if not state.get("publishers"):
        return {"missing_fields": [], "next_step": "strategist"}

    missing_fields = _missing_composer_fields(composer_data)
    if os.getenv("DEBUG_INTAKE") == "1":
        print("Supervisor missing composer fields:", missing_fields)
    if missing_fields:
        return {"missing_fields": missing_fields, "next_step": "clarify"}

    if not state.get("letters"):
        return {"missing_fields": [], "next_step": "composer"}

    return {"missing_fields": [], "next_step": "end"}


def _strategist_node(state: QueryLetterState) -> dict:
    strategist_data = state.get("strategist_data") or {}
    strategist_input = StrategistManuscript(**strategist_data)
    service = create_strategist_service()
    results = execute_strategist_pipeline(service, strategist_input)
    publishers = [
        Publisher(name=entry.publisher_name or entry.publisher_id, comps=entry.comps)
        for entry in results
    ]
    return {"publishers": publishers, "strategist_input": strategist_input}


def _composer_node(state: QueryLetterState) -> dict:
    composer_data = state.get("composer_data") or {}
    composer_input = Manuscript(**composer_data)
    options = ComposerOptions()
    payload = ComposerRequest(
        manuscript=composer_input,
        publishers=state["publishers"],
        options=options,
    )
    letters = compose_query_letters(payload)
    return {"letters": letters, "composer_input": composer_input}


def _intake_node(state: QueryLetterState) -> dict:
    user_message = (state.get("user_message") or "").strip()
    if not user_message:
        return {"user_message": "", "next_step": "supervisor"}

    missing_fields = state.get("missing_fields") or []
    parsed = parse_intake(user_message, missing_fields=missing_fields)

    strategist_data = dict(state.get("strategist_data") or {})
    composer_data = dict(state.get("composer_data") or {})

    if parsed.strategist:
        strategist_data.update(parsed.strategist.model_dump(exclude_none=True))
    if parsed.composer:
        composer_data.update(parsed.composer.model_dump(exclude_none=True))

    if os.getenv("DEBUG_INTAKE") == "1":
        print("Intake merged strategist_data:", strategist_data)
        print("Intake merged composer_data:", composer_data)

    return {
        "strategist_data": strategist_data,
        "composer_data": composer_data,
        "user_message": "",
        "missing_fields": [],
    }


def _clarify_node(state: QueryLetterState) -> dict:
    missing_fields = state.get("missing_fields") or []
    if not missing_fields:
        return {
            "assistant_message": "",
            "strategist_data": state.get("strategist_data"),
            "composer_data": state.get("composer_data"),
            "publishers": state.get("publishers"),
            "letters": state.get("letters"),
        }
    assistant_message = generate_clarification(missing_fields)
    return {
        "assistant_message": assistant_message,
        "strategist_data": state.get("strategist_data"),
        "composer_data": state.get("composer_data"),
        "publishers": state.get("publishers"),
        "letters": state.get("letters"),
    }


def _route_from_supervisor(state: QueryLetterState) -> str:
    return state.get("next_step", "end")


def build_query_letter_graph():
    if StateGraph is None:
        raise RuntimeError(
            "langgraph is not installed. Add it to requirements to use this graph."
        )

    graph = StateGraph(QueryLetterState)
    graph.add_node("supervisor", _supervisor_node)
    graph.add_node("intake", _intake_node)
    graph.add_node("strategist", _strategist_node)
    graph.add_node("composer", _composer_node)
    graph.add_node("clarify", _clarify_node)

    graph.set_entry_point("supervisor")
    graph.add_conditional_edges(
        "supervisor",
        _route_from_supervisor,
        {
            "intake": "intake",
            "clarify": "clarify",
            "strategist": "strategist",
            "composer": "composer",
            "end": END,
        },
    )
    graph.add_edge("intake", "supervisor")
    graph.add_edge("strategist", "supervisor")
    graph.add_edge("composer", "supervisor")
    graph.add_edge("clarify", END)
    return graph.compile()
