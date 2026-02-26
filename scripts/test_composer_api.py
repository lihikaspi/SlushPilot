import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.schemas.composer import ComposerRequest, LetterResult
from app.services.composer import (
    build_batched_composer_prompt,
    generate_query_letters_batch,
    load_fewshot_examples,
    render_query_letter,
)

def main() -> int:
    output_path = Path("composer_letters.md")
    publishers = [
        {
            "name": "Harborlight Literary",
            "comps": ["Legends & Lattes", "The Undertaking of Hart and Mercy"],
        },
        {
            "name": "Northbridge Books",
            "comps": ["The Power", "Station Eleven"],
        },
        {
            "name": "Blue Current Press",
            "comps": ["The Night Circus", "A Gentleman in Moscow"],
        },
        {
            "name": "Stonegate Publishing",
            "comps": ["The Silent Patient", "The Girl with the Dragon Tattoo"],
        },
        {
            "name": "Juniper House",
            "comps": ["We Were Liars", "Firekeeper's Daughter"],
        },
    ]

    users = [
        {
            "manuscript": {
                "title": "The Glass Orchard",
                "word_count": 93000,
                "genre": "Speculative Literary Fiction",
                "summary": (
                    "After a citywide blackout reveals a hidden orchard that only appears "
                    "at night, a grieving urban planner must decide whether to expose the "
                    "phenomenon or protect the community that has grown around it."
                ),
                "author_bio": (
                    "ALL FOR GLORY is a standalone novel inspired by my family's summers "
                    "in Northern Michigan. Five generations have rented the same cabin "
                    "every year, but no one has been able to prove it's haunted (yet). "
                    "As a queer author, it was important for me to write about queer teens "
                    "who challenge nostalgia and tradition. In 2023, I won the Write Team "
                    "Mentorship contest and worked on revising this manuscript with my "
                    "mentors."
                ),
                "author_name": "Dalia Noor",
            },
            "options": {
                "format": "classic_query_letter",
                "paraphrase_summary": False,
            },
        },
    ]

    lines = ["# Query Letters", ""]

    try:
        examples = load_fewshot_examples()
    except Exception as exc:
        print(f"Failed to load few-shot examples: {exc}")
        return 1

    for idx, user in enumerate(users, start=1):
        payload = ComposerRequest(
            manuscript=user["manuscript"],
            publishers=publishers,
            options=user["options"],
        )
        lines.append(f"# User {idx}: {user['manuscript']['author_name']}")
        lines.append("")

        results = []
        errors = []
        for publisher in payload.publishers:
            warnings = []
            if not publisher.comps:
                warnings.append("comps_missing")
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
                    errors.append(
                        f"{entry.publisher}: missing letter in batch response"
                    )
        except Exception as exc:
            errors.append(str(exc))
            for entry in results:
                entry.status = "error"

        for entry in results:
            lines.append(f"## Publisher: {entry.publisher}")
            lines.append(f"Status: {entry.status}")
            if entry.warnings:
                lines.append(f"Warnings: {', '.join(entry.warnings)}")
            lines.append("")
            lines.append(entry.letter.strip() if entry.letter else "[No letter returned]")
            lines.append("")

        if errors:
            lines.append("## Errors")
            lines.extend(errors)
            lines.append("")

    output_text = "\n".join(lines).strip() + "\n"
    output_path.write_text(output_text, encoding="utf-8")
    print(f"Saved response to {output_path.resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
