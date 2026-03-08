from typing import List, Optional

from pydantic import BaseModel, Field


class StrategistManuscript(BaseModel):
    title: str
    genre: str
    word_count: int
    blurb: str
    comparative_titles: List[str]
    target_audience: str


class HybridSearchQueries(BaseModel):
    semantic_query: str = Field(
        description=(
            "A descriptive paragraph capturing the thematic vibe and narrative style. "
            "Optimize for a dense vector search."
        )
    )
    lexical_keywords: List[str] = Field(
        description=(
            "List of 5-10 specific tropes, sub-genres, and comp authors. "
            "Optimize for exact keyword matching."
        )
    )


class PublisherScore(BaseModel):
    publisher_id: str
    publisher_name: Optional[str] = None
    score: int = Field(description="Relevance score from 1 to 10 based on fit.")
    reasoning: str = Field(description="Brief 1-sentence rationale for the score.")
    comps: List[str] = Field(
        description=(
            "Short list of relevant comp titles from recent publications that align "
            "with the manuscript."
        )
    )


class RerankedList(BaseModel):
    scored_publishers: List[PublisherScore]
