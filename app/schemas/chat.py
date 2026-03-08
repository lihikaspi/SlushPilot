from typing import List, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    project_id: str
    user_message: str


class LetterSaved(BaseModel):
    publisher: str
    query_letter_id: str


class ChatResponse(BaseModel):
    assistant_message: str
    letters_saved: List[LetterSaved] = Field(default_factory=list)
    current_step: str = ""
    error: Optional[str] = None
