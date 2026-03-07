import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

# Local imports
import config

app = FastAPI(title="Slush Pilot")

app.add_middleware(
    CORSMiddleware, #type: ignore
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Student(BaseModel):
    name: str
    email: str


class TeamInfoResponse(BaseModel):
    group_batch_order_number: str
    team_name: str
    students: List[Student]


class Step(BaseModel):
    module: str
    prompt: Dict[str, Any]
    response: Dict[str, Any]


class ExecuteRequest(BaseModel):
    prompt: str


class ExecuteResponse(BaseModel):
    status: str
    error: Optional[str] = None
    response: Optional[str] = None
    steps: List[Step] = []



@app.get("/api/team_info", response_model=TeamInfoResponse)
async def get_team_info():
    """Returns Technion student details."""
    return TeamInfoResponse(
        group_batch_order_number="3_4",
        team_name="ליהיא ליאור והראל",
        students=[
            Student(name="Lihi Kaspi", email="lihi.kaspi@campus.technion.ac.il"),
            Student(name="Harel Oved", email="harel.oved@campus.technion.ac.il"),
            Student(name="Lior Zaphir", email="lior.zaphir@campus.technion.ac.il")
        ]
    )


@app.get("/api/agent_info")
async def get_agent_info():
    """Returns agent metadata + how to use it."""
    return {
        "description": "Slush Pilot is an autonomous agent that helps authors find the right publishers and drafts personalized query letters.",
        "purpose": "To automate the book submission process for aspiring authors.",
        "prompt_template": {
            "template": "I have written a {genre} novel titled {title}. Help me find publishers and draft a letter."
        },
        "prompt_examples": [
            {
                "prompt": "I wrote a 90k word Sci-Fi novel called 'Mars Rising'.",
                "full_response": "I've identified 3 publishers matching Sci-Fi and drafted letters for each.",
                "steps": []
            }
        ]
    }


@app.get("/api/model_architecture")
async def get_model_architecture():
    """Returns the architecture diagram as a PNG."""
    return FileResponse(config.ARCHITECTURE_IMAGE, media_type="image/png")


@app.post("/api/execute", response_model=ExecuteResponse)
async def execute_agent(payload: ExecuteRequest):
    # logic to handle agent execution...
    # Example insertion logic for Supabase:
    # 1. Create entry in iterations table
    # 2. Process steps -> insert into steps table
    # 3. Process letters -> insert into letters table

    # Mocking for UI testing:
    return ExecuteResponse(
        status="success",
        response="I have analyzed your book and prepared letters for 2 publishers.",
        steps=[
            Step(module="GenreAnalysis", prompt={"text": payload.prompt}, response={"detected": "Fiction"}),
            Step(module="PublisherMatch", prompt={"genre": "Fiction"},
                 response={"matches": ["Penguin", "HarperCollins"]})
        ]
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)