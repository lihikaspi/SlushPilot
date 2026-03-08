import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

# Assuming these are your local imports
import config  # Contains PINECONE_API_KEY, SUPABASE_URL, etc.
import prompts  # Contains SYSTEM_PROMPT_CHAT, SYSTEM_PROMPT_LETTER, etc.

from langchain_openai import ChatOpenAI
from langchain_pinecone import PineconeVectorStore
from langchain_core.messages import HumanMessage, SystemMessage
from supabase import create_client, Client

app = FastAPI(title="Slush Pilot")


# --- 1. Pydantic Models (Schemas matching assignment) ---

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


# --- 2. Required API Endpoints ---

@app.get("/api/team_info", response_model=TeamInfoResponse)
async def get_team_info():
    """Returns Technion student details from the config."""
    batch_order_number = "3_4"
    team_name = "ליהיא ליאור והראל"
    students = [Student(name="Lihi Kaspi", email="lihi.kaspi@campus.technion.ac.il"),
                Student(name="Harel Oved", email="harel.oved@campus.technion.ac.il"),
                Student(name="Lior Zaphir", email="lior.zaphir@campus.technion.ac.il")]
    return TeamInfoResponse(
        group_batch_order_number=batch_order_number,
        team_name=team_name,
        students=students
    )


@app.get("/api/agent_info")
async def get_agent_info():
    """Returns agent metadata and prompt templates from prompts.py."""
    pass


@app.get("/api/model_architecture")
async def get_model_architecture():
    """Returns the architecture diagram PNG."""
    return FileResponse(config.ARCHITECTURE_IMAGE, media_type="image/png")


@app.post("/api/execute", response_model=ExecuteResponse)
async def execute_agent(payload: ExecuteRequest):
    """
    Main Logic:
    1. Search Pinecone for publishers (Trace step).
    2. Generate response using LangChain (Trace step).
    3. Save to Supabase (Optional for response, required for history).
    """
    steps_trace = []

    try:
        # Step A: Retrieval Module (Pinecone)
        # prompt_data = {"query": payload.prompt}
        # results = search_publishers(payload.prompt)
        # steps_trace.append(Step(module="Retriever", prompt=prompt_data, response=results))

        # Step B: Generation Module (LangChain)
        # response = generate_letter(payload.prompt, context=results)
        # steps_trace.append(Step(module="Generator", prompt=..., response=...))

        pass

    except Exception as e:
        return ExecuteResponse(status="error", error=str(e))


# --- 3. LangChain & DB Integration Placeholders ---

def get_vectorstore():
    """Initializes PineconeVectorStore via config.PINECONE_API_KEY."""
    pass


def get_supabase():
    """Initializes Supabase Client via config.SUPABASE_URL."""
    pass


def generate_letter(user_input: str, context: str):
    """Uses LangChain ChatOpenAI with prompts.SYSTEM_PROMPT_LETTER."""
    pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)