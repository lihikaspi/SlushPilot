import json
import re
from pathlib import Path
from typing import List

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

import config
from app.schemas.composer import ComposerOptions, Manuscript, Publisher


class QueryLetterSections(BaseModel):
    tone: str = Field(
        ...,
        description=(
            "Chosen tone for the letter. Select one of: professional, warm_professional, "
            "literary_professional, tense_professional."
        ),
    )
    personalization_reason: str = Field(
        ...,
        description=(
            "Why this publisher is a fit. Phrase as a clause that can follow "
            "'I am querying you because ...' without adding a leading period."
        ),
    )
    fit_compatible: bool = Field(
        ...,
        description=(
            "True if the publisher's strengths align with the manuscript's genre "
            "and audience; false if they conflict."
        ),
    )
    summary_paragraphs: List[str] = Field(
        ...,
        description="1-2 paragraphs summarizing the story with protagonist, goal, stakes.",
    )
    bio: str = Field(
        ...,
        description="1-2 factual sentences about the author and credentials.",
    )
    signoff: str = Field(
        default="Sincerely",
        description="A short signoff such as 'Sincerely' or 'Warmly'.",
    )


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
        "You are a query letter composer. Return JSON only that matches the schema "
        "described in the user message. Do not include markdown, commentary, or extra keys."
    )

    personalization = manuscript.personalization_notes or ""
    criteria = publisher.special_criteria or ""
    imprints = ", ".join(publisher.imprints) if publisher.imprints else "None"
    comps = ", ".join(publisher.comps) if publisher.comps else "None provided"

    example_block = "\n\n".join(
        f"Example {idx + 1}:\n{example}" for idx, example in enumerate(examples)
    )

    user_text = (
        f"Examples:\n{example_block}\n\n"
        "Task: Fill the JSON schema using the inputs below. Use the examples for tone only. "
        "Do NOT copy their structure into any field. Output JSON only.\n\n"
        "Schema:\n"
        "{\n"
        '  "tone": "professional",\n'
        '  "personalization_reason": "string",\n'
        '  "fit_compatible": true,\n'
        '  "summary_paragraphs": ["string", "..."],\n'
        '  "bio": "string",\n'
        '  "signoff": "Sincerely"\n'
        "}\n\n"
        f"Publisher name: {publisher.name}\n"
        f"Imprints: {imprints}\n"
        f"Personalization notes: {personalization or 'None provided'}\n"
        f"Publisher strength criteria: {criteria or 'None provided'}\n"
        f"Format: {options.format}\n\n"
        "Manuscript:\n"
        f"- Title: {manuscript.title}\n"
        f"- Word count: {manuscript.word_count}\n"
        f"- Genre: {manuscript.genre}\n"
        f"- Summary: {manuscript.summary}\n"
        f"- Paraphrase summary: {options.paraphrase_summary}\n"
        f"- Comps: {comps}\n"
        f"- Author name: {manuscript.author_name}\n"
        f"- Author bio: {manuscript.author_bio or 'None provided'}\n"
    )

    if not options.paraphrase_summary:
        user_text += (
            "\nInstruction: Use the summary text verbatim in the plot description "
            "section. Do not paraphrase or embellish it."
        )
    user_text += (
        "\nConstraints:\n"
        "- tone: choose one of professional, warm_professional, literary_professional, "
        "tense_professional based on the manuscript and publisher.\n"
        "- personalization_reason: clause only (no leading 'I am querying you because').\n"
        "- fit_compatible: set to false if criteria conflict with the manuscript genre.\n"
        "- summary_paragraphs: story summary only; do not include title/word count/genre, "
        "comps, bio, or closing.\n"
        "- bio: 1-2 factual sentences.\n"
        "- Use the chosen tone when writing summary and bio.\n"
    )

    return [SystemMessage(content=system_text), HumanMessage(content=user_text)]


def _normalize_clause(text: str) -> str:
    cleaned = text.strip()
    cleaned = re.sub(
        r"^(i am querying you because|i hope you will consider|because)\s+",
        "",
        cleaned,
        flags=re.IGNORECASE,
    ).strip()
    cleaned = re.sub(r"^[\W_]+", "", cleaned)
    if cleaned.endswith("."):
        cleaned = cleaned[:-1].strip()
    return cleaned


def _sanitize_summary_paragraphs(paragraphs: List[str]) -> List[str]:
    cleaned_paragraphs = []
    for paragraph in paragraphs:
        text = paragraph.strip()
        if not text:
            continue
        lowered = text.lower()
        if any(
            marker in lowered
            for marker in (
                "i am seeking representation",
                "i am querying you because",
                "dear ",
                "will appeal to readers",
                "thank you for your time",
                "sincerely",
                "warmly",
            )
        ):
            continue
        cleaned_paragraphs.append(text)
    return cleaned_paragraphs


def _sanitize_bio(bio: str, author_name: str) -> str:
    text = bio.strip()
    text = re.sub(r"\s+—\s+" + re.escape(author_name) + r"\s*$", "", text)
    return text.strip()


def _fallback_personalization(publisher: Publisher) -> str:
    if publisher.special_criteria:
        return publisher.special_criteria.strip()
    return "your publishing interests align with my manuscript"


def _format_word_count(word_count: int) -> str:
    return f"{word_count:,}"


def _join_comps(comps: List[str]) -> str:
    if not comps:
        return ""
    if len(comps) == 1:
        return comps[0]
    if len(comps) == 2:
        return f"{comps[0]} and {comps[1]}"
    return f"{', '.join(comps[:-1])}, and {comps[-1]}"


def _sanitize_comps(comps: List[str]) -> List[str]:
    cleaned = []
    for comp in comps:
        value = comp.strip()
        if not value:
            continue
        cleaned.append(value)
    if len(cleaned) > 3:
        cleaned = cleaned[:3]
    return cleaned


def _make_clause(text: str) -> str:
    cleaned = _normalize_clause(text)
    if not cleaned:
        return ""
    return cleaned[0].lower() + cleaned[1:]


def _build_personalization_clause(
    manuscript: Manuscript,
    publisher: Publisher,
    fit_compatible: bool,
) -> str:
    clauses = []
    fit = manuscript.personalization_notes or ""
    if fit and not fit_compatible:
        fit = ""
    fit_clause = _make_clause(fit)
    if fit_clause:
        clauses.append(fit_clause)

    criteria = publisher.special_criteria or ""
    criteria_clause = _make_clause(criteria)
    if criteria_clause:
        if not re.search(r"\byou\b", criteria_clause, flags=re.IGNORECASE):
            criteria_clause = f"you have {criteria_clause}"
        clauses.append(criteria_clause)

    if clauses:
        return " and ".join(clauses)
    return _fallback_personalization(publisher)


def render_query_letter(
    manuscript: Manuscript,
    publisher: Publisher,
    sections: QueryLetterSections,
    paraphrase_summary: bool,
) -> str:
    lines = []
    lines.append("Dear Acquisitions Team,")
    lines.append("")

    personalization = _build_personalization_clause(
        manuscript,
        publisher,
        sections.fit_compatible,
    )
    lines.append(
        "I am seeking representation for my "
        f"{manuscript.genre} novel, {manuscript.title}, "
        f"complete at {_format_word_count(manuscript.word_count)} words. "
        f"I am querying you because {personalization}."
    )
    lines.append("")

    if paraphrase_summary:
        summary_paragraphs = _sanitize_summary_paragraphs(
            sections.summary_paragraphs
        )
    else:
        summary_paragraphs = [manuscript.summary.strip()]

    for paragraph in summary_paragraphs:
        if paragraph.strip():
            lines.append(paragraph.strip())
            lines.append("")

    comps = _sanitize_comps(publisher.comps or [])
    if comps:
        comps_line = _join_comps(comps)
        lines.append(
            f"{manuscript.title} will appeal to readers of {comps_line}."
        )
        lines.append("")

    lines.append(_sanitize_bio(sections.bio, manuscript.author_name))
    lines.append("")
    lines.append(
        "Thank you for your time and consideration. The full manuscript is available "
        "upon request."
    )
    lines.append("")
    lines.append(f"{sections.signoff},")
    lines.append(manuscript.author_name)

    return "\n".join(lines).strip()


def generate_query_letter(
    messages: List,
    manuscript: Manuscript,
    publisher: Publisher,
    options: ComposerOptions,
) -> str:
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
    raw = response.content.strip()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Model did not return valid JSON: {exc}") from exc

    sections = QueryLetterSections.model_validate(data)
    return render_query_letter(
        manuscript,
        publisher,
        sections,
        paraphrase_summary=options.paraphrase_summary,
    )
