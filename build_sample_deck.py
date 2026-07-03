#!/usr/bin/env python3
"""Build the public sample Anki deck from the first N5/N4 vocabulary rows."""

import csv
from pathlib import Path

import genanki


MODEL_ID = 1607392320
DECK_ID = 2059400111
CARD_LIMIT = 20

CSV_PATH = Path(__file__).parent / "data" / "jlpt_n5_n4_vocab.csv"
OUT_PATH = Path(__file__).parent / "samples" / "easy-japanese-sample.apkg"
FULL_PACK_URL = "https://duct-tape2.github.io/japanese-anki-pack/"


def build():
    model = genanki.Model(
        MODEL_ID,
        "Easy Japanese Sample Card",
        fields=[
            {"name": "Japanese"},
            {"name": "Romaji"},
            {"name": "English"},
            {"name": "JLPT"},
            {"name": "PartOfSpeech"},
            {"name": "ExampleJP"},
            {"name": "ExampleEN"},
            {"name": "Notes"},
            {"name": "FullPackUrl"},
        ],
        templates=[
            {
                "name": "JP -> EN",
                "qfmt": """
                <div class="jp">{{Japanese}}</div>
                <div class="romaji">{{Romaji}}</div>
                """,
                "afmt": """
                {{FrontSide}}
                <hr>
                <div class="answer"><b>{{English}}</b></div>
                <div class="tag">{{JLPT}} - {{PartOfSpeech}}</div>
                <div class="example">
                  <div>{{ExampleJP}}</div>
                  <div class="example-en">{{ExampleEN}}</div>
                </div>
                <div class="notes">{{Notes}}</div>
                <div class="upgrade">Full pack: {{FullPackUrl}}</div>
                """,
            },
            {
                "name": "EN -> JP",
                "qfmt": """
                <div class="answer">{{English}}</div>
                <div class="tag">{{JLPT}} - {{PartOfSpeech}}</div>
                """,
                "afmt": """
                {{FrontSide}}
                <hr>
                <div class="jp"><b>{{Japanese}}</b></div>
                <div class="romaji">{{Romaji}}</div>
                <div class="example">
                  <div>{{ExampleJP}}</div>
                  <div class="example-en">{{ExampleEN}}</div>
                </div>
                <div class="upgrade">Full pack: {{FullPackUrl}}</div>
                """,
            },
        ],
        css="""
        .card {
          font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
          font-size: 18px;
          padding: 20px;
        }
        .jp { text-align: center; font-size: 32px; }
        .romaji { text-align: center; color: #666; margin-top: 8px; }
        .answer { text-align: center; font-size: 22px; }
        .tag { text-align: center; color: #0f766e; margin-top: 6px; }
        .example { margin-top: 14px; padding: 12px; background: #f6f7f9; border-radius: 8px; }
        .example-en { color: #666; margin-top: 6px; font-style: italic; }
        .notes { margin-top: 10px; color: #666; font-size: 13px; }
        .upgrade { margin-top: 16px; color: #444; font-size: 12px; text-align: center; }
        """,
    )

    deck = genanki.Deck(DECK_ID, "Easy Japanese :: Free JLPT N5/N4 Sample")

    count = 0
    with CSV_PATH.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if count >= CARD_LIMIT:
                break
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
                    FULL_PACK_URL,
                ],
            )
            deck.add_note(note)
            count += 1

    genanki.Package(deck).write_to_file(str(OUT_PATH))
    print(f"Built {OUT_PATH} ({count} notes, {count * 2} cards)")
    return count


if __name__ == "__main__":
    build()
