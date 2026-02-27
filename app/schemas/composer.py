from typing import List, Optional

from pydantic import BaseModel, Field


class Manuscript(BaseModel):
    title: str
    word_count: int
    genre: str
    summary: str
    detail_summary: Optional[str] = None
    author_bio: Optional[str] = None
    author_name: str
    personalization_notes: Optional[str] = None


class Publisher(BaseModel):
    name: str
    comps: Optional[List[str]] = None


class ComposerOptions(BaseModel):
    format: str = "classic_query_letter"
    paraphrase_summary: bool = True
    infer_detail_summary: bool = True


class ComposerRequest(BaseModel):
    manuscript: Manuscript
    publishers: List[Publisher]
    options: ComposerOptions = Field(default_factory=ComposerOptions)


class LetterResult(BaseModel):
    publisher: str
    letter: str
    status: str = "ok"
    warnings: List[str] = Field(default_factory=list)


class ComposerResponse(BaseModel):
    letters: List[LetterResult]
    errors: List[str] = Field(default_factory=list)
