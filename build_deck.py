#!/usr/bin/env python3
"""Build the paid Anki deck from the JLPT N5/N4 vocabulary CSV."""

import csv
import genanki
import random
from pathlib import Path

# Stable IDs so updates don't duplicate
MODEL_ID = 1607392319
DECK_ID = 2059400110

CSV_PATH = Path(__file__).parent / "data" / "jlpt_n5_n4_vocab.csv"
OUT_PATH = Path(__file__).parent / "dist" / "easy-japanese-jlpt-n5-n4.apkg"


def build():
    model = genanki.Model(
        MODEL_ID,
        "Easy Japanese JLPT Card",
        fields=[
            {"name": "Japanese"},
            {"name": "Romaji"},
            {"name": "English"},
            {"name": "JLPT"},
            {"name": "PartOfSpeech"},
            {"name": "ExampleJP"},
            {"name": "ExampleEN"},
            {"name": "Notes"},
        ],
        templates=[
            {
                "name": "JP → EN",
                "qfmt": """
                <div style='text-align:center; font-size: 32px; font-family: -apple-system, sans-serif;'>{{Japanese}}</div>
                <div style='text-align:center; color:#888; margin-top:8px;'>{{Romaji}}</div>
                """,
                "afmt": """
                {{FrontSide}}
                <hr>
                <div style='text-align:center; font-size:20px;'><b>{{English}}</b></div>
                <div style='text-align:center; color:#4ade80; margin-top:4px;'>{{JLPT}} · {{PartOfSpeech}}</div>
                <div style='margin-top:12px; padding:10px; background:#f5f5f5; border-radius:6px;'>
                <div>{{ExampleJP}}</div>
                <div style='color:#666; margin-top:4px; font-style:italic;'>{{ExampleEN}}</div>
                </div>
                <div style='margin-top:8px; font-size:12px; color:#888;'>{{Notes}}</div>
                """,
            },
            {
                "name": "EN → JP",
                "qfmt": """
                <div style='text-align:center; font-size: 24px; font-family: -apple-system, sans-serif;'>{{English}}</div>
                <div style='text-align:center; color:#888; margin-top:8px;'>{{JLPT}} · {{PartOfSpeech}}</div>
                """,
                "afmt": """
                {{FrontSide}}
                <hr>
                <div style='text-align:center; font-size:32px;'><b>{{Japanese}}</b></div>
                <div style='text-align:center; color:#888; margin-top:4px;'>{{Romaji}}</div>
                <div style='margin-top:12px; padding:10px; background:#f5f5f5; border-radius:6px;'>
                <div>{{ExampleJP}}</div>
                <div style='color:#666; margin-top:4px; font-style:italic;'>{{ExampleEN}}</div>
                </div>
                """,
            },
        ],
        css="""
        .card { font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 18px; padding: 20px; }
        """,
    )

    deck = genanki.Deck(DECK_ID, "Easy Japanese :: JLPT N5/N4 Vocabulary (Anime & J-Pop)")

    count = 0
    with CSV_PATH.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            note = genanki.Note(
                model=model,
                fields=[
                    row["japanese"],
                    row["romaji"],
                    row["english"],
                    row["jlpt"],
                    row["pos"],
                    row.get("example_jp", ""),
                    row.get("example_en", ""),
                    row.get("notes", ""),
                ],
            )
            deck.add_note(note)
            count += 1

    OUT_PATH.parent.mkdir(exist_ok=True)
    genanki.Package(deck).write_to_file(str(OUT_PATH))
    print(f"Built {OUT_PATH} ({count} cards)")
    return count


if __name__ == "__main__":
    build()
