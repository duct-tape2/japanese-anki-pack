#!/usr/bin/env python3
"""Build the private paid delivery ZIP.

The generated bundle is intentionally ignored by git. It can be delivered after
payment without publishing the paid assets in the public repository.
"""

from __future__ import annotations

import csv
import hashlib
import html
import re
import shutil
import subprocess
import zipfile
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import PageBreak, Paragraph, Preformatted, SimpleDocTemplate, Spacer


ROOT = Path(__file__).resolve().parent
BUNDLE_DIR = ROOT / "paid_bundle"
ZIP_PATH = ROOT / "paid_bundle.zip"
PRINTABLE_MD = BUNDLE_DIR / "PRINTABLE_COMPILATION.md"
PRINTABLE_PDF = BUNDLE_DIR / "easy-japanese-printable.pdf"
FULL_DECK = ROOT / "dist" / "easy-japanese-jlpt-full.apkg"
IDEAVAULT = Path.home() / "Documents" / "IdeaVault"
LANGS = ("en", "es", "vi")
PDF_FONT_PATH = Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf")
PDF_FONT = "PaidPackUnicode"


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9._-]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value or "lesson"


def strip_frontmatter(text: str) -> str:
    if text.startswith("---\n"):
        parts = text.split("\n---\n", 1)
        if len(parts) == 2:
            return parts[1].lstrip()
    return text


def find_lesson_files() -> list[Path]:
    lessons: list[Path] = []
    if IDEAVAULT.exists():
        for blog_dir in IDEAVAULT.rglob("global_japanese_blog"):
            for lang in LANGS:
                lessons.extend(blog_dir.rglob(f"{lang}.md"))
    return sorted(set(lessons))


def copy_lessons(lesson_files: list[Path]) -> dict[str, int]:
    counts = {lang: 0 for lang in LANGS}
    for src in lesson_files:
        lang = src.stem
        if lang not in counts:
            continue
        path_hash = hashlib.sha1(str(src.parent).encode("utf-8")).hexdigest()[:8]
        lesson_slug = f"{slugify(src.parent.name)}-{path_hash}"
        dest = BUNDLE_DIR / "lessons" / lesson_slug / f"{lang}.md"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
        counts[lang] += 1
    return counts


def count_csv_rows(path: Path) -> int:
    with path.open(encoding="utf-8") as f:
        return sum(1 for _ in csv.DictReader(f))


def build_full_deck() -> None:
    subprocess.run(["python3", str(ROOT / "build_deck.py")], cwd=ROOT, check=True)


def write_bundle_readme(counts: dict[str, int], note_count: int) -> None:
    readme = f"""# Easy Japanese Paid Pack

Thank you for buying the Easy Japanese: Anime & J-Pop Vocabulary Pack.

## Included Files

- `anki/easy-japanese-jlpt-full.apkg` - Anki import file with {note_count} notes / {note_count * 2} review cards.
- `lessons/` - {sum(counts.values())} lesson files:
  - English: {counts.get("en", 0)}
  - Spanish: {counts.get("es", 0)}
  - Vietnamese: {counts.get("vi", 0)}
- `data/` - JLPT vocabulary CSV files.
- `PRINTABLE_COMPILATION.md` - printable English lesson compilation.
- `easy-japanese-printable.pdf` - PDF version of the English compilation.

## Importing The Anki Deck

1. Open Anki Desktop.
2. Choose `File -> Import`.
3. Select `anki/easy-japanese-jlpt-full.apkg`.
4. Keep the default import options unless you already customized this deck.

## Copyright And Use

This pack contains original educational commentary, vocabulary breakdowns, and
author-written example sentences. It does not redistribute full song lyrics,
anime subtitles, manga panels, or audio files.

Personal use only. Please do not resell, repost, or redistribute this ZIP.
"""
    (BUNDLE_DIR / "README.md").write_text(readme, encoding="utf-8")


def write_printable_md() -> list[Path]:
    english_lessons = sorted((BUNDLE_DIR / "lessons").glob("*/en.md"))
    parts = [
        "# Easy Japanese Printable Compilation\n",
        "This compilation contains the English lesson files from the paid pack.\n",
        "It is designed for printing or reading alongside the Anki deck.\n",
    ]
    for lesson in english_lessons:
        text = strip_frontmatter(lesson.read_text(encoding="utf-8"))
        parts.append("\n\\newpage\n")
        parts.append(text)
    PRINTABLE_MD.write_text("\n".join(parts), encoding="utf-8")
    return english_lessons


def paragraph_style(name: str, base: ParagraphStyle, **kwargs) -> ParagraphStyle:
    return ParagraphStyle(name=name, parent=base, **kwargs)


def markdown_to_story(markdown_text: str):
    if not PDF_FONT_PATH.exists():
        raise FileNotFoundError(f"PDF font not found: {PDF_FONT_PATH}")
    if PDF_FONT not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(PDF_FONT, str(PDF_FONT_PATH)))

    styles = getSampleStyleSheet()
    body = paragraph_style(
        "BodyCJK",
        styles["BodyText"],
        fontName=PDF_FONT,
        fontSize=9.5,
        leading=13,
        spaceAfter=5,
    )
    h1 = paragraph_style(
        "H1CJK",
        styles["Heading1"],
        fontName=PDF_FONT,
        fontSize=18,
        leading=23,
        spaceBefore=8,
        spaceAfter=10,
    )
    h2 = paragraph_style(
        "H2CJK",
        styles["Heading2"],
        fontName=PDF_FONT,
        fontSize=14,
        leading=18,
        spaceBefore=9,
        spaceAfter=7,
    )
    h3 = paragraph_style(
        "H3CJK",
        styles["Heading3"],
        fontName=PDF_FONT,
        fontSize=11.5,
        leading=15,
        spaceBefore=7,
        spaceAfter=5,
    )
    code = paragraph_style(
        "CodeCJK",
        styles["Code"],
        fontName=PDF_FONT,
        fontSize=7.5,
        leading=9,
        leftIndent=6,
    )

    story = []
    in_code = False
    code_lines: list[str] = []

    def flush_code() -> None:
        nonlocal code_lines
        if code_lines:
            story.append(Preformatted("\n".join(code_lines), code))
            story.append(Spacer(1, 4))
            code_lines = []

    for raw_line in markdown_text.splitlines():
        line = raw_line.rstrip()
        if line.strip() == "\\newpage":
            flush_code()
            story.append(PageBreak())
            continue
        if line.startswith("```"):
            if in_code:
                flush_code()
                in_code = False
            else:
                in_code = True
            continue
        if in_code:
            code_lines.append(line)
            continue
        if not line.strip():
            story.append(Spacer(1, 4))
            continue
        if line.startswith("|"):
            story.append(Preformatted(line, code))
            continue

        escaped = html.escape(line)
        escaped = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", escaped)
        escaped = re.sub(r"\*(.+?)\*", r"<i>\1</i>", escaped)
        escaped = re.sub(r"`(.+?)`", r"<b>\1</b>", escaped)

        if escaped.startswith("# "):
            story.append(Paragraph(escaped[2:], h1))
        elif escaped.startswith("## "):
            story.append(Paragraph(escaped[3:], h2))
        elif escaped.startswith("### "):
            story.append(Paragraph(escaped[4:], h3))
        elif escaped.startswith("#### "):
            story.append(Paragraph(escaped[5:], h3))
        elif escaped.startswith("- "):
            story.append(Paragraph(f"- {escaped[2:]}", body))
        elif re.match(r"^\d+\\. ", escaped):
            story.append(Paragraph(escaped, body))
        else:
            story.append(Paragraph(escaped, body))
    flush_code()
    return story


def write_pdf() -> None:
    doc = SimpleDocTemplate(
        str(PRINTABLE_PDF),
        pagesize=A4,
        rightMargin=16 * mm,
        leftMargin=16 * mm,
        topMargin=16 * mm,
        bottomMargin=18 * mm,
    )

    def footer(canvas, document):
        canvas.saveState()
        canvas.setFont(PDF_FONT, 8)
        canvas.drawRightString(194 * mm, 10 * mm, f"Page {document.page}")
        canvas.restoreState()

    story = markdown_to_story(PRINTABLE_MD.read_text(encoding="utf-8"))
    doc.build(story, onFirstPage=footer, onLaterPages=footer)


def zip_bundle() -> None:
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(BUNDLE_DIR.rglob("*")):
            if path.is_file():
                zf.write(path, path.relative_to(BUNDLE_DIR.parent))


def main() -> None:
    if BUNDLE_DIR.exists():
        shutil.rmtree(BUNDLE_DIR)
    (BUNDLE_DIR / "anki").mkdir(parents=True)
    (BUNDLE_DIR / "data").mkdir(parents=True)

    build_full_deck()
    shutil.copy2(FULL_DECK, BUNDLE_DIR / "anki" / FULL_DECK.name)
    for csv_file in sorted((ROOT / "data").glob("*.csv")):
        shutil.copy2(csv_file, BUNDLE_DIR / "data" / csv_file.name)

    lesson_files = find_lesson_files()
    counts = copy_lessons(lesson_files)
    note_count = count_csv_rows(ROOT / "data" / "jlpt_full.csv")

    write_bundle_readme(counts, note_count)
    english_lessons = write_printable_md()
    write_pdf()
    zip_bundle()

    print(f"Bundle: {ZIP_PATH}")
    print(f"ZIP bytes: {ZIP_PATH.stat().st_size}")
    print(f"Lessons: {sum(counts.values())} total ({counts})")
    print(f"English printable lessons: {len(english_lessons)}")
    print(f"Anki: {note_count} notes / {note_count * 2} review cards")


if __name__ == "__main__":
    main()
