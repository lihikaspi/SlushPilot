from pathlib import Path
from typing import List

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

import config
from app.schemas.composer import ComposerOptions, Manuscript, Publisher


def load_fewshot_examples() -> List[str]:
    base_dir = Path(__file__).resolve().parents[2] / "composer" / "letters"
    if not base_dir.exists():
        raise FileNotFoundError(f"Missing composer letters directory: {base_dir}")
    examples: List[str] = []
    for folder in sorted(base_dir.iterdir()):
        if not folder.is_dir():
            continue
        modified_path = folder / "modified"
        if modified_path.exists():
            examples.append(modified_path.read_text(encoding="utf-8").strip())
    if not examples:
        raise FileNotFoundError(f"No few-shot examples found in: {base_dir}")
    return examples


def build_composer_prompt(
    manuscript: Manuscript,
    publisher: Publisher,
    options: ComposerOptions,
    examples: List[str],
) -> List:
    system_text = (
        "You are a query letter composer. Write a single query letter that follows "
        "standard industry format: personalized opening, title/word count/genre, "
        "1-2 paragraphs of story with stakes, comps (if provided), brief bio, and a "
        "professional closing. Keep it under one page. Do not add analysis."
    )

    personalization = publisher.fit_notes or manuscript.personalization_notes or ""
    comps = ", ".join(manuscript.comps) if manuscript.comps else "None provided"
    imprints = ", ".join(publisher.imprints) if publisher.imprints else "None"
    agent_name = publisher.agent_name or "Agent"

    example_block = "\n\n".join(
        f"Example {idx + 1}:\n{example}" for idx, example in enumerate(examples)
    )

    user_text = (
        f"Examples:\n{example_block}\n\n"
        "Task: Write a new query letter using the inputs below.\n\n"
        f"Publisher name: {publisher.name}\n"
        f"Agent name: {agent_name}\n"
        f"Imprints: {imprints}\n"
        f"Fit notes: {personalization}\n"
        f"Tone: {options.tone}\n"
        f"Format: {options.format}\n\n"
        "Manuscript:\n"
        f"- Title: {manuscript.title}\n"
        f"- Word count: {manuscript.word_count}\n"
        f"- Genre: {manuscript.genre}\n"
        f"- Summary: {manuscript.summary}\n"
        f"- Comps: {comps}\n"
        f"- Author name: {manuscript.author_name}\n"
        f"- Author bio: {manuscript.author_bio or 'None provided'}\n"
    )

    return [SystemMessage(content=system_text), HumanMessage(content=user_text)]


def generate_query_letter(messages: List) -> str:
    temperature = 0
    if "gpt-5" in (config.CHAT_MODEL or "").lower():
        # gpt-5 family only supports temperature=1
        temperature = 1
    model = ChatOpenAI(
        api_key=config.OPENAI_API_KEY,
        base_url=config.BASE_URL,
        model=config.CHAT_MODEL,
        temperature=temperature,
    )
    response = model.invoke(messages)
    return response.content.strip()
