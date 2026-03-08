import logging
import time

from fastapi import APIRouter
from fastapi.responses import FileResponse

import config
from app.agents.clarify import generate_clarification
from app.agents.composer import compose_query_letters
from app.services.supabase_client import get_supabase_client
from app.agents.intake import parse_intake
from app.agents.strategist import (
    StrategistManuscript,
    create_strategist_service,
    formulate_queries,
    rerank_publishers,
    retrieve_candidates,
)
from app.schemas.composer import (
    ComposerOptions,
    ComposerRequest,
    Manuscript,
    Publisher,
)
from app.schemas.core import ExecuteRequest, ExecuteResponse, Step, Student, TeamInfoResponse

logger = logging.getLogger(__name__)


router = APIRouter()


@router.get("/api/team_info", response_model=TeamInfoResponse)
async def get_team_info() -> TeamInfoResponse:
    batch_order_number = "3_4"
    team_name = "ליהיא ליאור והראל"
    students = [
        Student(name="Lihi Kaspi", email="lihi.kaspi@campus.technion.ac.il"),
        Student(name="Harel Oved", email="harel.oved@campus.technion.ac.il"),
        Student(name="Lior Zaphir", email="lior.zaphir@campus.technion.ac.il"),
    ]
    return TeamInfoResponse(
        group_batch_order_number=batch_order_number,
        team_name=team_name,
        students=students,
    )


PROMPT_TEMPLATE = (
    "Title: {title}\n"
    "Genre: {genre}\n"
    "Word Count: {word_count}\n"
    "Blurb: {blurb}\n"
    "Comparative Titles: {comp1}, {comp2}\n"
    "Target Audience: {target_audience}\n"
    "Author Name: {author_name}\n"
    "Author Bio: {author_bio}"
)

EXAMPLE_PROMPT = (
    "Title: The Glass Garden\n"
    "Genre: Literary Fiction\n"
    "Word Count: 80000\n"
    "Blurb: A reclusive botanist in 1920s England discovers that a high frequency emitted "
    "by a New World orchid opens brief windows into the past. As she journeys deeper into "
    "the greenhouse passages, she must choose between rewriting her family's tragedy and "
    "preserving the fragile timeline she already knows.\n"
    "Comparative Titles: The Time Traveler's Wife, The Overstory\n"
    "Target Audience: Adult literary fiction readers who enjoy magical realism and "
    "historical settings\n"
    "Author Name: Jane Smith\n"
    "Author Bio: Jane Smith holds an MFA in Creative Writing from the University of Iowa "
    "and has published short fiction in The Paris Review and Tin House."
)

EXAMPLE_RESPONSE = (
    "Generated 5 personalized query letters for matching publishers. "
    "Each letter includes an opening paragraph tailored to the publisher's catalog, "
    "a story summary, author bio, and professional closing. "
    "Publishers matched based on genre alignment and comparative title overlap."
)

EXAMPLE_STEPS = [
    {
        "module": "Intake",
        "prompt": {
            "system": "You extract structured fields for a query-letter assistant. "
            "Return JSON only that matches the schema. "
            "Use null for unknown values and do not invent details.",
            "user": "Strategist fields: title, genre, word_count, blurb, "
            "comparative_titles, target_audience. ..."
        },
        "response": {
            "strategist": {
                "title": "The Glass Garden",
                "genre": "Literary Fiction",
                "word_count": 80000,
                "blurb": "A reclusive botanist discovers time travel through orchids...",
                "comparative_titles": ["The Time Traveler's Wife", "The Overstory"],
                "target_audience": "Adult literary fiction readers"
            },
            "composer": {
                "title": "The Glass Garden",
                "word_count": 80000,
                "genre": "Literary Fiction",
                "summary": "A reclusive botanist discovers time travel through orchids...",
                "author_name": "Jane Smith",
                "author_bio": "Jane Smith holds an MFA from Iowa..."
            }
        }
    },
    {
        "module": "Strategist - Query Formulation",
        "prompt": {
            "system": "You are an expert literary agent AI configuring a database search.",
            "user": "Analyze this manuscript profile and generate search queries..."
        },
        "response": {
            "semantic_query": "Literary fiction novel with magical realism elements...",
            "lexical_keywords": ["literary fiction", "magical realism", "time travel",
                                 "botanical", "historical"]
        }
    },
    {
        "module": "Strategist - Reranking",
        "prompt": {
            "system": "You are a master publishing strategist. Identify the absolute "
            "best fit for this specific manuscript.",
            "user": "Evaluate the following list of publishers against the manuscript..."
        },
        "response": {
            "top_publishers": [
                {"name": "Algonquin Books", "score": 9, "reasoning": "Strong literary fiction catalog"},
                {"name": "Tin House Books", "score": 8, "reasoning": "Publishes magical realism"}
            ]
        }
    },
    {
        "module": "Composer",
        "prompt": {
            "system": "You are a query letter composer. Return JSON only.",
            "user": "Generate personalized query letters for each publisher..."
        },
        "response": {
            "letters_generated": 5,
            "sample_opening": "Dear Acquisitions Team, Given your catalog's emphasis on "
            "literary fiction with inventive premises..."
        }
    }
]


@router.get("/api/agent_info")
async def get_agent_info():
    return {
        "description": (
            "Slush Pilot is a multi-agent query letter assistant that helps authors "
            "find matching publishers via hybrid semantic/keyword search over a Pinecone "
            "vector database, then composes personalized query letters using few-shot "
            "examples and structured LLM output."
        ),
        "purpose": (
            "Given a manuscript description (title, genre, word count, blurb, comps, "
            "target audience, author info), the agent: (1) parses the input into "
            "structured fields (Intake), (2) generates search queries and retrieves "
            "candidate publishers from Pinecone (Strategist - Query Formulation), "
            "(3) reranks publishers by manuscript fit (Strategist - Reranking), and "
            "(4) composes personalized query letters for the top matches (Composer)."
        ),
        "prompt_template": {
            "template": PROMPT_TEMPLATE,
        },
        "prompt_examples": [
            {
                "prompt": EXAMPLE_PROMPT,
                "full_response": EXAMPLE_RESPONSE,
                "steps": EXAMPLE_STEPS,
            }
        ],
    }


@router.get("/api/model_architecture")
async def get_model_architecture():
    return FileResponse(config.ARCHITECTURE_IMAGE, media_type="image/jpeg")


def _sanitize_for_pg(obj):
    """Remove \\u0000 null bytes that PostgreSQL rejects in text/jsonb."""
    import json
    return json.loads(json.dumps(obj).replace("\\u0000", ""))


def _persist_execution(
    user_id: int,
    iteration: int,
    prompt: str,
    steps_trace: list[Step],
    response_text: str,
    good_letters: list | None = None,
):
    """Save execution results to steps and letters tables."""
    try:
        supabase = get_supabase_client()

        # Determine next message number for this user+iteration
        existing = (
            supabase.table("steps")
            .select("message")
            .eq("user", user_id)
            .eq("iteration", iteration)
            .order("message", desc=True)
            .limit(1)
            .execute()
        )
        next_msg = (existing.data[0]["message"] + 1) if existing.data else 1

        # Insert step row
        steps_data = _sanitize_for_pg([s.model_dump() for s in steps_trace])
        supabase.table("steps").insert({
            "user": user_id,
            "iteration": iteration,
            "message": next_msg,
            "input": prompt,
            "steps": steps_data,
            "response": response_text.replace("\u0000", ""),
        }).execute()

        # Insert letters
        if good_letters:
            # Get current max id to work around sequence issues
            max_id_res = (
                supabase.table("letters")
                .select("id")
                .order("id", desc=True)
                .limit(1)
                .execute()
            )
            next_letter_id = (max_id_res.data[0]["id"] + 1) if max_id_res.data else 1

            for lr in good_letters:
                supabase.table("letters").insert({
                    "id": next_letter_id,
                    "user": user_id,
                    "iteration": iteration,
                    "publisher": lr.publisher,
                    "content": lr.letter,
                }).execute()
                next_letter_id += 1

        logger.info("Persisted execution: user=%d iter=%d msg=%d", user_id, iteration, next_msg)
    except Exception:
        logger.exception("Failed to persist execution results")


@router.post("/api/execute", response_model=ExecuteResponse)
async def execute_agent(payload: ExecuteRequest) -> ExecuteResponse:
    """
    Single-shot autonomous pipeline: intake → strategist → composer.
    Bypasses the interactive LangGraph. All manuscript info must be in the prompt.
    """
    steps_trace: list[Step] = []

    try:
        # ── 0. CONTEXT: gather previous inputs from this iteration ──
        full_prompt = payload.prompt
        try:
            supabase = get_supabase_client()
            prev_steps = (
                supabase.table("steps")
                .select("input")
                .eq("user", payload.user_id)
                .eq("iteration", payload.iteration)
                .order("message", desc=False)
                .execute()
            )
            if prev_steps.data:
                previous_inputs = [s["input"] for s in prev_steps.data]
                previous_inputs.append(payload.prompt)
                full_prompt = "\n\n".join(previous_inputs)
        except Exception:
            logger.debug("Could not fetch previous steps, using current prompt only")

        # ── 1. INTAKE: parse prompt into structured fields ──
        t0 = time.time()
        parsed, intake_trace = parse_intake(full_prompt, return_trace=True)
        logger.info("Execute: intake completed in %.1fs", time.time() - t0)

        steps_trace.append(Step(
            module="Intake",
            prompt={"system": intake_trace["system"], "user": intake_trace["user"]},
            response=intake_trace["response"],
        ))

        # Build strategist and composer data from intake
        strategist_data = {}
        composer_data = {}
        if parsed.strategist:
            strategist_data = parsed.strategist.model_dump(exclude_none=True)
        if parsed.composer:
            composer_data = parsed.composer.model_dump(exclude_none=True)

        # Cross-populate blurb <-> summary
        if not strategist_data.get("blurb") and composer_data.get("summary"):
            strategist_data["blurb"] = composer_data["summary"]
        if not composer_data.get("summary") and strategist_data.get("blurb"):
            composer_data["summary"] = strategist_data["blurb"]

        # Validate all required fields (same checks as the graph)
        missing = []
        if not (strategist_data.get("title") or "").strip():
            missing.append("strategist.title")
        if not (strategist_data.get("genre") or "").strip():
            missing.append("strategist.genre")
        if not (strategist_data.get("blurb") or "").strip():
            missing.append("strategist.blurb")
        if (strategist_data.get("word_count") or 0) <= 0 and (composer_data.get("word_count") or 0) <= 0:
            missing.append("strategist.word_count")
        if not strategist_data.get("comparative_titles"):
            missing.append("strategist.comparative_titles")
        if not (strategist_data.get("target_audience") or "").strip():
            missing.append("strategist.target_audience")
        if not (composer_data.get("author_name") or "").strip():
            missing.append("composer.author_name")
        author_bio = (composer_data.get("author_bio") or "").strip()
        if not author_bio or len(author_bio) < 30:
            missing.append("composer.author_bio")

        if missing:
            clarification = generate_clarification(missing)
            response_text = clarification
            _persist_execution(
                payload.user_id, payload.iteration, payload.prompt,
                steps_trace, response_text,
            )
            return ExecuteResponse(
                status="clarification",
                response=clarification,
                steps=steps_trace,
            )

        # Ensure defaults for optional fields that passed validation
        if not strategist_data.get("word_count"):
            strategist_data["word_count"] = composer_data.get("word_count", 0)
        if not strategist_data.get("comparative_titles"):
            strategist_data["comparative_titles"] = []
        if not strategist_data.get("target_audience"):
            strategist_data["target_audience"] = ""

        # ── 2. STRATEGIST - QUERY FORMULATION ──
        t1 = time.time()
        service = create_strategist_service()
        manuscript = StrategistManuscript(**strategist_data)
        queries, qf_trace = formulate_queries(service, manuscript, return_trace=True)
        logger.info("Execute: query formulation completed in %.1fs", time.time() - t1)

        steps_trace.append(Step(
            module="Strategist - Query Formulation",
            prompt={"system": qf_trace["system"], "user": qf_trace["user"]},
            response=qf_trace["response"],
        ))

        # ── 3. RETRIEVAL (Pinecone — no LLM call) ──
        t2 = time.time()
        candidates = retrieve_candidates(service, queries)
        logger.info("Execute: retrieval found %d candidates in %.1fs",
                     len(candidates), time.time() - t2)

        if not candidates:
            return ExecuteResponse(
                status="error",
                error="No publisher candidates found in the database.",
                steps=steps_trace,
            )

        # ── 4. STRATEGIST - RERANKING ──
        t3 = time.time()
        scored, rerank_trace = rerank_publishers(
            service, manuscript, candidates, return_trace=True
        )
        scored.sort(key=lambda x: x.score, reverse=True)
        top_results = scored[:5]
        logger.info("Execute: reranking completed in %.1fs", time.time() - t3)

        # Fill in publisher names from candidate metadata
        candidate_names = {
            m.id: (m.metadata or {}).get("publisher_name") for m in candidates
        }
        for result in top_results:
            if not result.publisher_name:
                result.publisher_name = candidate_names.get(result.publisher_id)

        steps_trace.append(Step(
            module="Strategist - Reranking",
            prompt={"system": rerank_trace["system"], "user": rerank_trace["user"]},
            response={"scored_publishers": rerank_trace["response"]},
        ))

        # Build publisher list for composer
        publishers = [
            Publisher(name=s.publisher_name or s.publisher_id, comps=s.comps)
            for s in top_results
        ]

        # ── 5. COMPOSER: generate query letters ──
        # Ensure composer has minimum required fields
        if not composer_data.get("title"):
            composer_data["title"] = strategist_data.get("title", "")
        if not composer_data.get("word_count"):
            composer_data["word_count"] = strategist_data.get("word_count", 0)
        if not composer_data.get("genre"):
            composer_data["genre"] = strategist_data.get("genre", "")
        if not composer_data.get("summary"):
            composer_data["summary"] = strategist_data.get("blurb", "")
        if not composer_data.get("author_name"):
            composer_data["author_name"] = "The Author"

        t4 = time.time()
        composer_manuscript = Manuscript(**{
            k: v for k, v in composer_data.items()
            if k in Manuscript.model_fields
        })
        composer_trace = []
        letters = compose_query_letters(
            ComposerRequest(
                manuscript=composer_manuscript,
                publishers=publishers,
                options=ComposerOptions(),
            ),
            trace_log=composer_trace,
        )
        logger.info("Execute: composer completed in %.1fs", time.time() - t4)

        if composer_trace:
            steps_trace.append(Step(
                module="Composer",
                prompt={
                    "system": composer_trace[0]["system"],
                    "user": composer_trace[0]["user"][:2000] + "..." if len(composer_trace[0]["user"]) > 2000 else composer_trace[0]["user"],
                },
                response={"raw_llm_output": composer_trace[0]["response"][:3000] + "..." if len(composer_trace[0]["response"]) > 3000 else composer_trace[0]["response"]},
            ))

        # Build response text
        good_letters = [lr for lr in letters.letters if lr.status == "ok" and lr.letter]
        if good_letters:
            parts = []
            for lr in good_letters:
                parts.append(f"=== Query Letter for {lr.publisher} ===\n\n{lr.letter}")
            response_text = (
                f"Generated {len(good_letters)} personalized query letters:\n\n"
                + "\n\n".join(parts)
            )
            _persist_execution(
                payload.user_id, payload.iteration, payload.prompt,
                steps_trace, response_text, good_letters,
            )
            return ExecuteResponse(
                status="ok", response=response_text, steps=steps_trace
            )
        else:
            error_detail = "; ".join(letters.errors) if letters.errors else "Unknown error"
            error_text = f"Letter generation failed: {error_detail}"
            _persist_execution(
                payload.user_id, payload.iteration, payload.prompt,
                steps_trace, error_text,
            )
            return ExecuteResponse(
                status="error",
                error=error_text,
                steps=steps_trace,
            )

    except Exception as e:
        logger.exception("Execute error")
        _persist_execution(
            payload.user_id, payload.iteration, payload.prompt,
            steps_trace, f"Error: {e}",
        )
        return ExecuteResponse(status="error", error=str(e), steps=steps_trace)
