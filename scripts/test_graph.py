from pathlib import Path
import os
import sys
from typing import Dict

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

os.environ.setdefault("DEBUG_INTAKE", "1")

from app.graphs.query_letter_graph import build_query_letter_graph
from app.schemas.composer import ComposerResponse


def main() -> None:
    graph = build_query_letter_graph()

    state: Dict = {
        "composer_data": {
            "author_name": "Riley Quinn",
            "author_bio": (
                "I am a Seattle-based writer and former investigative "
                "journalist with essays published in regional magazines."
            ),
        }
    }

    while True:
        user_message = input("\nHello! how can I help you today? ").strip()
        state["user_message"] = user_message
        result = graph.invoke(state)
        if os.getenv("DEBUG_INTAKE") == "1":
            print("Result keys:", sorted(result.keys()))
            if "assistant_message" in result:
                print("Result assistant_message length:", len(result.get("assistant_message") or ""))

        if result.get("errors"):
            print("Errors:")
            for error in result["errors"]:
                print(f"- {error}")
            return

        assistant_message = result.get("assistant_message")
        if assistant_message:
            print(f"\nAssistant: {assistant_message}")
            state.update(result)
            continue

        letters = result.get("letters")
        if isinstance(letters, ComposerResponse):
            print("\nGenerated letters:")
            for entry in letters.letters:
                print(f"\n=== {entry.publisher} ===")
                print(entry.letter)
            return

        state.update(result)


if __name__ == "__main__":
    main()
