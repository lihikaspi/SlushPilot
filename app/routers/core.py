from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

import config
import prompts
from app.schemas.core import ExecuteRequest, ExecuteResponse, Student, TeamInfoResponse


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
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/api/model_architecture")
async def get_model_architecture():
    """Returns the architecture diagram PNG."""
    return FileResponse(config.ARCHITECTURE_IMAGE, media_type="image/png")


@router.post("/api/execute", response_model=ExecuteResponse)
async def execute_agent(payload: ExecuteRequest) -> ExecuteResponse:
    """
    Main Logic:
    1. Search Pinecone for publishers (Trace step).
    2. Generate response using LangChain (Trace step).
    3. Save to Supabase (Optional for response, required for history).
    """
    _ = prompts
    return ExecuteResponse(status="error", error="Not implemented")
