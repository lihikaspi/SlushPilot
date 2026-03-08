import logging
import time

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

import config
import prompts
from app.schemas.core import ExecuteRequest, ExecuteResponse, Step, Student, TeamInfoResponse
from app.graphs.query_letter_graph import build_query_letter_graph
from app.services.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


router = APIRouter()


@router.get("/api/team_info", response_model=TeamInfoResponse)
async def get_team_info() -> TeamInfoResponse:
    """Returns Technion student details from the config."""
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


@router.get("/api/agent_info")
async def get_agent_info():
    """Returns agent metadata and prompt templates from prompts.py."""
    return {
        "agent_name": "Slush Pilot",
        "description": "A multi-agent query letter assistant that helps authors find matching publishers and compose personalized query letters.",
        "architecture": "LangGraph supervisor pattern with 5 specialist nodes",
        "nodes": [
            {
                "name": "intake",
                "purpose": "Extract structured manuscript fields from user messages",
                "prompt_template": "You extract structured fields for a query-letter assistant. Return JSON only that matches the schema. Use null for unknown values and do not invent details.",
            },
            {
                "name": "clarify",
                "purpose": "Ask clarification questions for missing manuscript details",
                "prompt_template": "You are a helpful assistant collecting missing details for a query-letter tool. Ask a concise, friendly clarification question.",
            },
            {
                "name": "strategist",
                "purpose": "Search Pinecone for matching publishers and rerank with LLM",
                "prompt_template": "You are an expert literary agent AI configuring a database search. / You are a master publishing strategist. Identify the absolute best fit for this specific manuscript.",
            },
            {
                "name": "composer",
                "purpose": "Generate personalized query letters using few-shot examples",
                "prompt_template": "You are a query letter composer. Return JSON only that matches the schema described in the user message. Do not include markdown, commentary, or extra keys.",
            },
            {
                "name": "confirm",
                "purpose": "Parse user confirmation before generating letters",
                "prompt_template": "Decide whether the user explicitly agrees to proceed with writing query letters. Return JSON only. Use decision=yes only if the user clearly agrees.",
            },
        ],
        "examples": [
            {"user": "I wrote a 80,000 word literary fiction novel called 'The Glass Garden' about a botanist who discovers time travel through plants.", "description": "Typical first message with manuscript details"},
            {"user": "yes, go ahead and write the letters", "description": "Confirmation to proceed with letter generation"},
        ],
    }


@router.get("/api/model_architecture")
async def get_model_architecture():
    """Returns the architecture diagram PNG."""
    return FileResponse(config.ARCHITECTURE_IMAGE, media_type="image/png")


@router.post("/api/execute", response_model=ExecuteResponse)
async def execute_agent(payload: ExecuteRequest) -> ExecuteResponse:
    """
    Runs the full LangGraph query-letter pipeline in a single invocation.
    Traces each graph node as a Step for the assignment grading rubric.
    """
    _ = prompts
    steps_trace: list[Step] = []

    try:
        input_state = {"user_message": payload.prompt}

        t0 = time.time()
        graph = build_query_letter_graph()
        final_state = graph.invoke(input_state)
        elapsed = time.time() - t0
        logger.info("Execute: graph completed in %.1fs", elapsed)

        # Build trace steps from the final state
        if final_state.get("intake_data"):
            steps_trace.append(Step(
                module="Intake",
                prompt={"user_message": payload.prompt},
                response={"intake_data": str(final_state["intake_data"])},
            ))

        if final_state.get("matched_publishers"):
            steps_trace.append(Step(
                module="Strategist",
                prompt={"genre": str(final_state.get("intake_data", {}).get("strategist", {}))},
                response={"publishers_found": len(final_state["matched_publishers"])},
            ))

        if final_state.get("draft_letters"):
            steps_trace.append(Step(
                module="Composer",
                prompt={"publishers": [p.get("name", "") for p in final_state.get("matched_publishers", [])]},
                response={"letters_generated": len(final_state["draft_letters"])},
            ))

        # Extract assistant message
        assistant_message = final_state.get("assistant_message", "")

        # Save letters to Supabase if generated
        if final_state.get("draft_letters"):
            supabase = get_supabase_client()
            for letter in final_state["draft_letters"]:
                pub = letter.get("publisher", "Unknown")
                content = letter.get("content", "")
                supabase.table("query_letters").upsert({
                    "project_id": "execute-api",
                    "publisher": pub,
                    "content": content,
                }).execute()

        return ExecuteResponse(
            status="success",
            response=assistant_message,
            steps=steps_trace,
        )

    except Exception as e:
        logger.exception("Execute error")
        return ExecuteResponse(status="error", error=str(e), steps=steps_trace)
