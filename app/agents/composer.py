import json
from pathlib import Path
from typing import List

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

import config
from app.schemas.composer import (
    ComposerOptions,
    ComposerRequest,
    ComposerResponse,
    LetterResult,
    Manuscript,
    Publisher,
)


class QueryLetterSections(BaseModel):
    tone: str = Field(
        ...,
        description=(
            "Chosen tone for the letter. Select one of: professional, warm_professional, "
            "literary_professional, tense_professional."
        ),
    )
    opening_personalization: str = Field(
        ...,
        description=(
            "1-2 sentences explaining fit with the agency/publisher. Mention the genre "
            "fit and, if comps are provided, reference them as similar titles."
        ),
    )
    summary_paragraphs: List[str] = Field(
        ...,
        description="1-2 paragraphs summarizing the story with protagonist, goal, stakes.",
    )
    detail_paragraph: str = Field(
        ...,
        description=(
            "A short paragraph with specific character, location, and unique details "
            "that deepen the summary. Must be distinct from the summary."
        ),
    )
    bio: str = Field(
        ...,
        description="1-2 factual sentences about the author and credentials.",
    )
    signoff: str = Field(
        default="Sincerely",
        description="A short signoff such as 'Sincerely' or 'Warmly'.",
    )


class BatchedPublisherSections(BaseModel):
    publisher: str = Field(..., description="Publisher name matching the input list.")
    tone: str = Field(
        ...,
        description=(
            "Chosen tone for the letter. Select one of: professional, warm_professional, "
            "literary_professional, tense_professional."
        ),
    )
    opening_personalization: str = Field(
        ...,
        description=(
            "1-2 sentences explaining fit with the agency/publisher. Mention the genre "
            "fit and, if comps are provided, reference them as similar titles."
        ),
    )
    summary_paragraphs: List[str] = Field(
        ...,
        description="1-2 paragraphs summarizing the story with protagonist, goal, stakes.",
    )
    detail_paragraph: str = Field(
        ...,
        description=(
            "A short paragraph with specific character, location, and unique details "
            "that deepen the summary. Must be distinct from the summary."
        ),
    )
    bio: str = Field(
        ...,
        description="1-2 factual sentences about the author and credentials.",
    )
    signoff: str = Field(
        default="Sincerely",
        description="A short signoff such as 'Sincerely' or 'Warmly'.",
    )


class BatchedQueryLetterResponse(BaseModel):
    letters: List[BatchedPublisherSections]


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
    return examples[:4]


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

    comps = ", ".join(publisher.comps) if publisher.comps else "None provided"

    example_block = "\n\n".join(
        f"Example {idx + 1}:\n{example}" for idx, example in enumerate(examples)
    )

    format_guidance = (
        "Section 1: Your Query’s Opening\n"
        "Show you targeted the agent for a reason and quickly introduce the novel "
        "with title, word count, and genre. If no personalization is provided, keep "
        "the opening focused on the novel without inventing agent-specific details.\n\n"
        "Section 2: The Story\n"
        "Summarize the book in one or two paragraphs with clear protagonist, goal, "
        "stakes, and a few specific details. Avoid a full plot rundown.\n\n"
        "Section 3: Your Bio\n"
        "Share any relevant writing credentials or background in 1–2 sentences.\n\n"
        "Section 4: The Closing\n"
        "End with a short, polite closing and manuscript availability."
    )

    user_text = (
        f"Examples:\n{example_block}\n\n"
        "Task: Fill the JSON schema using the inputs below. Use the examples to guide "
        "voice and natural phrasing. Output JSON only.\n\n"
        "Format guidance:\n"
        f"{format_guidance}\n\n"
        "Use opening_personalization for the opening fit paragraph. It should mention "
        "the genre fit with the publisher and, if comps are provided, cite those comps "
        "as similar titles. This paragraph will appear before the "
        "\"I'm hoping you will consider my ...\" line.\n\n"
        "Important: opening_personalization must NOT repeat the book title or word "
        "count, and must NOT include the phrase \"I'm hoping you will consider\".\n\n"
        "Important: summary_paragraphs must NOT repeat the book title or word count.\n"
        "Important: detail_paragraph must be clearly separate from the summary. "
        "If detail_summary is provided, use it as the primary source. If it is not "
        "provided and infer_detail_summary is true, infer from the summary. If "
        "infer_detail_summary is false and detail_summary is missing, keep the "
        "detail_paragraph brief and avoid introducing new plot points.\n\n"
        "Style: Avoid em dashes or dash-heavy sentences; prefer periods or commas.\n\n"
        "Schema:\n"
        "{\n"
        '  "tone": "professional",\n'
        '  "opening_personalization": "string",\n'
        '  "summary_paragraphs": ["string", "..."],\n'
        '  "detail_paragraph": "string",\n'
        '  "bio": "string",\n'
        '  "signoff": "Sincerely"\n'
        "}\n\n"
        f"Publisher name: {publisher.name}\n"
        f"Publisher comps: {comps}\n"
        f"Format: {options.format}\n\n"
        "Manuscript:\n"
        f"- Title: {manuscript.title}\n"
        f"- Word count: {manuscript.word_count}\n"
        f"- Genre: {manuscript.genre}\n"
        f"- Summary: {manuscript.summary}\n"
        f"- Detail summary: {manuscript.detail_summary or 'None provided'}\n"
        f"- Paraphrase summary: {options.paraphrase_summary}\n"
        f"- Infer detail summary: {options.infer_detail_summary}\n"
        f"- Author name: {manuscript.author_name}\n"
        f"- Author bio: {manuscript.author_bio or 'None provided'}\n"
    )

    if not options.paraphrase_summary:
        user_text += (
            "\nInstruction: Use the summary text verbatim in the plot description "
            "section. Do not paraphrase or embellish it."
        )

    return [SystemMessage(content=system_text), HumanMessage(content=user_text)]


def build_batched_composer_prompt(
    manuscript: Manuscript,
    publishers: List[Publisher],
    options: ComposerOptions,
    examples: List[str],
) -> List:
    system_text = (
        "You are a query letter composer. Return JSON only that matches the schema "
        "described in the user message. Do not include markdown, commentary, or extra keys."
    )

    example_block = "\n\n".join(
        f"Example {idx + 1}:\n{example}" for idx, example in enumerate(examples)
    )

    format_guidance = (
        "Section 1: Your Query’s Opening\n"
        "Show you targeted the agent for a reason and quickly introduce the novel "
        "with title, word count, and genre. If no personalization is provided, keep "
        "the opening focused on the novel without inventing agent-specific details.\n\n"
        "Section 2: The Story\n"
        "Summarize the book in one or two paragraphs with clear protagonist, goal, "
        "stakes, and a few specific details. Avoid a full plot rundown.\n\n"
        "Section 3: Your Bio\n"
        "Share any relevant writing credentials or background in 1–2 sentences.\n\n"
        "Section 4: The Closing\n"
        "End with a short, polite closing and manuscript availability."
    )

    publisher_lines = []
    for idx, publisher in enumerate(publishers, start=1):
        comps = ", ".join(publisher.comps) if publisher.comps else "None provided"
        publisher_lines.append(f"{idx}. {publisher.name} (comps: {comps})")
    publishers_block = "\n".join(publisher_lines) if publisher_lines else "None"

    user_text = (
        f"Examples:\n{example_block}\n\n"
        "Task: Fill the JSON schema using the inputs below. Use the examples to guide "
        "voice and natural phrasing. Output JSON only.\n\n"
        "Format guidance:\n"
        f"{format_guidance}\n\n"
        "Use opening_personalization for the opening fit paragraph. It should mention "
        "the genre fit with the publisher and, if comps are provided, cite those comps "
        "as similar titles. This paragraph will appear before the "
        "\"I'm hoping you will consider my ...\" line.\n\n"
        "Important: opening_personalization must NOT repeat the book title or word "
        "count, and must NOT include the phrase \"I'm hoping you will consider\".\n\n"
        "Important: summary_paragraphs must NOT repeat the book title or word count.\n"
        "Important: detail_paragraph must be clearly separate from the summary. "
        "If detail_summary is provided, use it as the primary source. If it is not "
        "provided and infer_detail_summary is true, infer from the summary. If "
        "infer_detail_summary is false and detail_summary is missing, keep the "
        "detail_paragraph brief and avoid introducing new plot points.\n\n"
        "Style: Avoid em dashes or dash-heavy sentences; prefer periods or commas.\n\n"
        "Schema:\n"
        "{\n"
        '  "letters": [\n'
        "    {\n"
        '      "publisher": "Publisher Name",\n'
        '      "tone": "professional",\n'
        '      "opening_personalization": "string",\n'
        '      "summary_paragraphs": ["string", "..."],\n'
        '      "detail_paragraph": "string",\n'
        '      "bio": "string",\n'
        '      "signoff": "Sincerely"\n'
        "    }\n"
        "  ]\n"
        "}\n\n"
        "Publishers (return one entry per publisher, in the same order):\n"
        f"{publishers_block}\n\n"
        f"Format: {options.format}\n\n"
        "Manuscript:\n"
        f"- Title: {manuscript.title}\n"
        f"- Word count: {manuscript.word_count}\n"
        f"- Genre: {manuscript.genre}\n"
        f"- Summary: {manuscript.summary}\n"
        f"- Detail summary: {manuscript.detail_summary or 'None provided'}\n"
        f"- Paraphrase summary: {options.paraphrase_summary}\n"
        f"- Infer detail summary: {options.infer_detail_summary}\n"
        f"- Author name: {manuscript.author_name}\n"
        f"- Author bio: {manuscript.author_bio or 'None provided'}\n"
    )

    if not options.paraphrase_summary:
        user_text += (
            "\nInstruction: Use the summary text verbatim in the plot description "
            "section. Do not paraphrase or embellish it."
        )

    return [SystemMessage(content=system_text), HumanMessage(content=user_text)]


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


def _signoff_for_tone(tone: str, fallback: str) -> str:
    normalized = (tone or "").strip().lower()
    if normalized == "warm_professional":
        return "Warmly"
    if normalized == "literary_professional":
        return "Sincerely"
    if normalized == "tense_professional":
        return "Sincerely"
    if normalized == "professional":
        return "Sincerely"
    return fallback or "Sincerely"


def render_query_letter(
    manuscript: Manuscript,
    publisher: Publisher,
    sections: QueryLetterSections,
    paraphrase_summary: bool,
) -> str:
    lines = []
    lines.append("Dear Acquisitions Team,")
    lines.append("")

    if sections.opening_personalization.strip():
        lines.append(sections.opening_personalization.strip())
        lines.append("")

    lines.append(
        "I'm hoping you will consider my "
        f"{manuscript.genre} novel, {manuscript.title}, "
        f"complete at {_format_word_count(manuscript.word_count)} words."
    )
    lines.append("")

    if paraphrase_summary:
        summary_paragraphs = sections.summary_paragraphs
    else:
        summary_paragraphs = [manuscript.summary.strip()]

    for paragraph in summary_paragraphs:
        cleaned_paragraph = paragraph.strip()
        lowered = cleaned_paragraph.lower()
        if lowered.startswith("i'm hoping you will consider"):
            cleaned_paragraph = cleaned_paragraph.split(".", 1)[-1].strip()
        elif lowered.startswith("i am seeking representation"):
            cleaned_paragraph = cleaned_paragraph.split(".", 1)[-1].strip()
        if cleaned_paragraph:
            sentences = [s.strip() for s in cleaned_paragraph.split(".") if s.strip()]
            filtered_sentences = []
            title_lower = manuscript.title.lower()
            word_count_token = _format_word_count(manuscript.word_count)
            for sentence in sentences:
                sentence_lower = sentence.lower()
                if title_lower in sentence_lower:
                    continue
                if word_count_token in sentence:
                    continue
                if str(manuscript.word_count) in sentence:
                    continue
                filtered_sentences.append(sentence)
            cleaned_paragraph = ". ".join(filtered_sentences).strip()
        if cleaned_paragraph:
            lines.append(cleaned_paragraph)
            lines.append("")

    detail_paragraph = sections.detail_paragraph.strip()
    if detail_paragraph:
        lines.append(detail_paragraph)
        lines.append("")

    comps = _sanitize_comps(publisher.comps or [])
    if comps:
        comps_line = _join_comps(comps)
        lines.append(
            f"{manuscript.title} will appeal to readers of {comps_line} "
            "because of its shared genre and tonal style."
        )
        lines.append("")

    lines.append(sections.bio.strip())
    lines.append("")
    lines.append(
        "Thank you for your time and consideration. The full manuscript is available "
        "upon request."
    )
    lines.append("")
    signoff = _signoff_for_tone(sections.tone, sections.signoff)
    lines.append(f"{signoff},")
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


def generate_query_letters_batch(
    messages: List,
    manuscript: Manuscript,
    publishers: List[Publisher],
    options: ComposerOptions,
) -> List[tuple[Publisher, QueryLetterSections]]:
    temperature = 0
    if "gpt-5" in (config.CHAT_MODEL or "").lower():
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

    batch = BatchedQueryLetterResponse.model_validate(data)
    sections_by_publisher = {
        entry.publisher: QueryLetterSections(
            tone=entry.tone,
            opening_personalization=entry.opening_personalization,
            summary_paragraphs=entry.summary_paragraphs,
            detail_paragraph=entry.detail_paragraph,
            bio=entry.bio,
            signoff=entry.signoff,
        )
        for entry in batch.letters
    }

    results = []
    for publisher in publishers:
        sections = sections_by_publisher.get(publisher.name)
        if not sections:
            raise ValueError(f"Missing letter for publisher: {publisher.name}")
        results.append((publisher, sections))
    return results


def compose_query_letters(payload: ComposerRequest) -> ComposerResponse:
    if not payload.publishers:
        raise ValueError("publishers list cannot be empty")

    errors = []
    results = []
    examples = load_fewshot_examples()

    for publisher in payload.publishers:
        warnings = []
        if not publisher.comps:
            warnings.append("comps_missing")
        if not payload.manuscript.personalization_notes:
            warnings.append("personalization_missing")

        results.append(
            LetterResult(
                publisher=publisher.name,
                letter="",
                warnings=warnings,
            )
        )

    try:
        messages = build_batched_composer_prompt(
            manuscript=payload.manuscript,
            publishers=payload.publishers,
            options=payload.options,
            examples=examples,
        )
        batch_sections = generate_query_letters_batch(
            messages=messages,
            manuscript=payload.manuscript,
            publishers=payload.publishers,
            options=payload.options,
        )
        letters_by_publisher = {
            publisher.name: render_query_letter(
                manuscript=payload.manuscript,
                publisher=publisher,
                sections=sections,
                paraphrase_summary=payload.options.paraphrase_summary,
            )
            for publisher, sections in batch_sections
        }
        for entry in results:
            entry.letter = letters_by_publisher.get(entry.publisher, "")
            if not entry.letter:
                entry.status = "error"
                errors.append(f"{entry.publisher}: missing letter in batch response")
    except Exception as exc:
        errors.append(str(exc))
        for entry in results:
            entry.status = "error"

    return ComposerResponse(letters=results, errors=errors)
