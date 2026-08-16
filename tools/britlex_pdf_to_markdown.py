#!/usr/bin/env python3
"""Convert the britlex "5000 important English words" PDF into import files.

The PDF ships with word list sections:
  - main list (5000 words + derived words, with transcription + translation)
  - international words (1502)
  - elementary words (602, word + translation, no transcription)

Output is written in the app's markdown import format
(`word | transcription | translation`) because CSV parsing splits on commas and
many translations contain commas.

Requires `pdftotext` (poppler) on PATH.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import TextIO

Entry = dict[str, str | None]

ENTRY_RE = re.compile(r"^(?:(\d+)\s+)?(.+?)\s+\[(.+?)\]\s*(.*)$")
CYRILLIC_RE = re.compile(r"[а-яёА-ЯЁ]")
TRAILING_MARKER_RE = re.compile(r"\s*(?:\(\d+\)|\d+)$")


def clean_transcription(transcription: str) -> str:
    """Fix typos present in the source PDF's transcription column."""
    tr = transcription.strip()
    had_cyrillic = bool(CYRILLIC_RE.search(tr))
    tr = CYRILLIC_RE.sub("", tr)
    if had_cyrillic:
        tr = tr.rstrip("-").strip()
    if tr.startswith("'"):
        tr = "ˈ" + tr[1:]
    tr = tr.rstrip("!").strip()
    tr = TRAILING_MARKER_RE.sub("", tr).strip()
    tr = tr.replace(",", ", ")
    return re.sub(r"\s{2,}", " ", tr).strip()


def extract_text(pdf: Path) -> str:
    pdftotext = shutil.which("pdftotext")
    if pdftotext is None:
        sys.exit("pdftotext (poppler) is required but not found on PATH")
    result = subprocess.run(
        [pdftotext, "-raw", str(pdf), "-"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.replace("\x0c", "\n")


def section_lines(lines: list[str], marker: re.Pattern[str], after: int = 0) -> int:
    for i, line in enumerate(lines):
        if marker.search(line):
            return i + after
    raise ValueError(f"section marker not found: {marker.pattern}")


def parse_entries(lines: list[str], start: int, end: int) -> list[Entry]:
    entries: list[Entry] = []
    cur: Entry | None = None

    def flush() -> None:
        nonlocal cur
        if cur is not None:
            entries.append(cur)
            cur = None

    for line in lines[start:end]:
        line = line.strip()
        if not line:
            continue
        m = ENTRY_RE.match(line)
        if m:
            num, word, transcription, translation = m.groups()
            if cur is not None and cur.get("frag"):
                num = cur["num"] or num
                word = f"{cur['word']} {word}".strip()
            else:
                flush()
            cur = {
                "num": num,
                "word": word.strip(),
                "transcription": transcription.strip(),
                "translation": translation.strip(),
                "frag": False,
            }
            continue
        if re.fullmatch(r"\d+", line):
            flush()
            cur = {"num": line, "word": "", "transcription": "", "translation": "", "frag": True}
            continue
        if re.search(r"[A-Za-z]", line) and re.search(r"[а-яёА-ЯЁ]", line):
            flush()
            parts = line.split(" ", 1)
            cur = {
                "num": None,
                "word": parts[0].strip(),
                "transcription": "",
                "translation": parts[1].strip() if len(parts) > 1 else "",
                "frag": False,
            }
            continue
        if re.search(r"[A-Za-z]", line):
            if cur is None:
                cur = {"num": None, "word": "", "transcription": "", "translation": "", "frag": True}
            cur["word"] = f"{cur['word']} {line}".strip()
            continue
        if cur is None:
            cur = {"num": None, "word": "", "transcription": "", "translation": "", "frag": False}
        cur["translation"] = f"{cur['translation']} {line}".strip()
    flush()
    return entries


def parse_elementary(lines: list[str], start: int) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for raw in lines[start:]:
        line = raw.strip()
        if not line:
            continue
        m = re.match(r"^([A-Za-z][A-Za-z0-9 /(),\-]*?)\s+([а-яёА-ЯЁ0-9].*)$", line)
        if m:
            pairs.append((m.group(1).strip(), m.group(2).strip()))
    return pairs


def write_section(out: TextIO, entries: list[Entry], include_num: bool) -> tuple[int, int]:
    """Write entries as `word | transcription | translation` rows.

    Rows without a translation are dropped (the importer rejects them).
    Returns (written, dropped).
    """
    dropped = 0
    for entry in entries:
        word = entry["word"]
        translation = entry["translation"]
        if not word or not translation:
            dropped += 1
            print(f"  dropped: {word or '(empty word)'} -> {translation!r}")
            continue
        transcription = clean_transcription(entry["transcription"] or "")
        out.write(f"{word} | {transcription} | {translation}\n")
    return len(entries) - dropped, dropped


def write_elementary(out: TextIO, pairs: list[tuple[str, str]]) -> None:
    for word, translation in pairs:
        out.write(f"{word} | {translation}\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path, help="path to the britlex PDF")
    parser.add_argument(
        "-o",
        "--out-dir",
        type=Path,
        default=Path("."),
        help="directory for generated import files",
    )
    args = parser.parse_args()

    raw = extract_text(args.pdf)
    lines = raw.split("\n")

    main_start = section_lines(lines, re.compile(r"^\s*1\s+arouse"))
    intl_start = section_lines(lines, re.compile(r"^Интернациональные слова"))
    elem_start = section_lines(lines, re.compile(r"^Слова элементарного уровня"))
    intl_first = section_lines(
        lines,
        re.compile(r"^\s*1\s+absolute"),
        after=0,
    )
    if intl_first < intl_start or intl_first >= elem_start:
        intl_first = next(
            i for i in range(intl_start, elem_start) if re.match(r"^\s*1\s+absolute", lines[i])
        )

    main_entries = parse_entries(lines, main_start, intl_start)
    intl_entries = parse_entries(lines, intl_first, elem_start)
    elementary = parse_elementary(lines, elem_start + 6)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    files = {
        "5000-main.md": main_entries,
        "1502-international.md": intl_entries,
    }
    for name, entries in files.items():
        with (args.out_dir / name).open("w", encoding="utf-8") as fh:
            written, dropped = write_section(fh, entries, include_num=False)
        print(f"{name}: {written} rows, {dropped} dropped (empty translation)")
    with (args.out_dir / "602-elementary.md").open("w", encoding="utf-8") as fh:
        write_elementary(fh, elementary)
    print(f"602-elementary.md: {len(elementary)} rows")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
