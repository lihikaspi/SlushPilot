from typing import Optional

from openai import OpenAI
from pydantic import BaseModel, Field

import config


class ConfirmationResult(BaseModel):
    decision: str = Field(
        description="One of: yes, no, unclear."
    )


def parse_confirmation(user_message: str) -> Optional[bool]:
    if not user_message.strip():
        return None
    if not config.OPENAI_API_KEY:
        raise ValueError("Missing OPENAI_API_KEY")

    client = OpenAI(api_key=config.OPENAI_API_KEY, base_url=config.BASE_URL)

    system_text = (
        "Decide whether the user explicitly agrees to proceed with writing query "
        "letters. Return JSON only. Use decision=yes only if the user clearly agrees. "
        "Use decision=no if they clearly decline. Otherwise use decision=unclear."
    )

    response = client.beta.chat.completions.parse(
        model=config.CHAT_MODEL,
        messages=[
            {"role": "system", "content": system_text},
            {"role": "user", "content": user_message},
        ],
        response_format=ConfirmationResult,
    )
    parsed = response.choices[0].message.parsed
    decision = (parsed.decision or "").strip().lower()
    if decision == "yes":
        return True
    if decision == "no":
        return False
    return None
