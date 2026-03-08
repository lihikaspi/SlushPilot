import os
from typing import List, Optional

from openai import OpenAI
from pydantic import BaseModel, Field

import config


class StrategistDraft(BaseModel):
    title: Optional[str] = None
    genre: Optional[str] = None
    word_count: Optional[int] = None
    blurb: Optional[str] = None
    comparative_titles: Optional[List[str]] = None
    target_audience: Optional[str] = None


class ComposerDraft(BaseModel):
    title: Optional[str] = None
    word_count: Optional[int] = None
    genre: Optional[str] = None
    summary: Optional[str] = None
    author_name: Optional[str] = None
    detail_summary: Optional[str] = None
    author_bio: Optional[str] = None
    personalization_notes: Optional[str] = None


class IntakeResult(BaseModel):
    strategist: Optional[StrategistDraft] = None
    composer: Optional[ComposerDraft] = None
    missing_fields: List[str] = Field(default_factory=list)


def parse_intake(user_message: str, missing_fields: Optional[List[str]] = None) -> IntakeResult:
    if not config.OPENAI_API_KEY:
        raise ValueError("Missing OPENAI_API_KEY")

    client = OpenAI(api_key=config.OPENAI_API_KEY, base_url=config.BASE_URL)

    system_text = (
        "You extract structured fields for a query-letter assistant. "
        "Return JSON only that matches the schema. "
        "Use null for unknown values and do not invent details."
    )

    fields_text = (
        "Strategist fields: title, genre, word_count, blurb, comparative_titles, "
        "target_audience.\n"
        "Composer fields: title, word_count, genre, summary, author_name, "
        "detail_summary, author_bio, personalization_notes.\n"
        "Always include strategist/composer objects with any extracted values."
    )

    if missing_fields:
        fields_text += (
            "\nMissing fields to prioritize:\n"
            + "\n".join(f"- {field}" for field in missing_fields)
        )

    user_text = f"{fields_text}\n\nUser message:\n{user_message}"

    response = client.beta.chat.completions.parse(
        model=config.CHAT_MODEL,
        messages=[
            {"role": "system", "content": system_text},
            {"role": "user", "content": user_text},
        ],
        response_format=IntakeResult,
    )
    parsed = response.choices[0].message.parsed
    if os.getenv("DEBUG_INTAKE") == "1":
        print("Intake parsed JSON:")
        print(parsed.model_dump())
    return parsed
