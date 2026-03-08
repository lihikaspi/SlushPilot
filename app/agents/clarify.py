from typing import List

from openai import OpenAI

import config


FIELD_HINTS = {
    "strategist.title": "the book title",
    "strategist.genre": "the genre",
    "strategist.word_count": "the approximate word count",
    "strategist.blurb": "a short blurb (1–3 sentences)",
    "strategist.comparative_titles": "2–3 comparable published titles",
    "strategist.target_audience": "the target readers (age range/interests)",
    "composer.title": "the book title",
    "composer.word_count": "the approximate word count",
    "composer.genre": "the genre",
    "composer.summary": "a fuller summary of the story",
    "composer.author_name": "the author name",
    "composer.author_bio": "a brief author bio for the query letter (1–3 sentences). If you have writing credentials, mention them — publications, awards, an MFA, or selection for a prestigious conference or residency. If you don't have formal credentials, that's completely fine — just share what makes you the right person to tell this story (personal connection, professional expertise, life experience, etc.)",
}


def generate_clarification(missing_fields: List[str]) -> str:
    if not config.OPENAI_API_KEY:
        raise ValueError("Missing OPENAI_API_KEY")

    client = OpenAI(api_key=config.OPENAI_API_KEY, base_url=config.BASE_URL)

    system_text = (
        "You are a helpful assistant collecting missing details for a query-letter tool. "
        "Ask a concise, friendly clarification question. "
        "Start with something like 'Thanks — I'm still missing a few details. Could you provide:' "
        "then list what's needed. "
        "Acknowledge what the user already provided and only ask for what is still missing. "
        "Avoid bullet lists unless there are more than 4 items."
    )

    hints = [FIELD_HINTS.get(field, field) for field in missing_fields]
    user_text = "Missing information:\n" + "\n".join(f"- {hint}" for hint in hints)

    response = client.chat.completions.create(
        model=config.CHAT_MODEL,
        messages=[
            {"role": "system", "content": system_text},
            {"role": "user", "content": user_text},
        ],
    )
    return (response.choices[0].message.content or "").strip()
