#!/usr/bin/env python3
"""Generate dictionary-backed study notes for One Punch Man Season 1."""

from __future__ import annotations

import json
import importlib.util
import re
import sys
import time
from pathlib import Path

import fugashi
from deep_translator import GoogleTranslator, MyMemoryTranslator
from jamdict import Jamdict
from pykakasi import kakasi

ANIME_DIR = Path(__file__).resolve().parent
REPO_ROOT = ANIME_DIR.parent
OUTPUT_DIR = ANIME_DIR / "study_guides"
SOURCE_DIR = ANIME_DIR / "captions"
CACHE_PATH = REPO_ROOT / "shared_translation_cache.json"

# Reuse the tokenizer, romanizer, and JMdict helpers without duplicating them.
common_path = REPO_ROOT / "jujutsu_kaisen" / "generate_study_guides.py"
common_spec = importlib.util.spec_from_file_location("study_guide_common", common_path)
if common_spec is None or common_spec.loader is None:
    raise RuntimeError(f"Unable to load shared study-guide helpers from {common_path}")
common = importlib.util.module_from_spec(common_spec)
common_spec.loader.exec_module(common)
breakdown = common.breakdown
display_text = common.display_text
romanize = common.romanize


def timestamp_parts(value: str) -> tuple[str, str]:
    start, end = (part.strip() for part in value.split("-->", 1))
    return start, end


def parse_and_collapse(path: Path) -> list[tuple[str, str]]:
    """Collapse only adjacent identical OCR captions, extending their time span."""
    parsed: list[tuple[str, str, str]] = []
    for raw in re.split(r"\n\s*\n", path.read_text(encoding="utf-8-sig").strip()):
        lines = [line.strip() for line in raw.splitlines() if line.strip()]
        if len(lines) < 3 or "-->" not in lines[1]:
            continue
        text = " ".join(lines[2:]).strip()
        if not text or text.startswith("Edited at https://subtitletools.com"):
            continue
        start, end = timestamp_parts(lines[1])
        parsed.append((start, end, text))

    collapsed: list[list[str]] = []
    for start, end, text in parsed:
        if collapsed and collapsed[-1][2] == text:
            collapsed[-1][1] = end
        else:
            collapsed.append([start, end, text])
    return [(f"{start} --> {end}", text) for start, end, text in collapsed]


def save_cache(cache: dict[str, str]) -> None:
    CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    episode = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    if not 1 <= episode <= 12:
        raise SystemExit("Episode must be between 1 and 12")
    source = SOURCE_DIR / f"episode_{episode:02d}.ja.srt"
    output = OUTPUT_DIR / f"one_punch_man_s01e{episode:02d}_complete_study.md"
    if not source.exists():
        raise SystemExit(f"Subtitle not found: {source}")

    cache = json.loads(CACHE_PATH.read_text(encoding="utf-8")) if CACHE_PATH.exists() else {}
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    converter = kakasi()
    tagger = fugashi.Tagger()
    dictionary = Jamdict()
    google = GoogleTranslator(source="ja", target="en")
    fallback = MyMemoryTranslator(source="japanese", target="english")
    sections = []
    new_translations = 0

    for number, (timestamp, original) in enumerate(parse_and_collapse(source), 1):
        visible = display_text(original)
        english = cache.get(original)
        if not english:
            try:
                time.sleep(0.3)
                english = google.translate(original)
                if not english:
                    raise ValueError("Google returned an empty translation")
            except Exception as google_exc:
                try:
                    english = fallback.translate(original)
                    if not english:
                        raise ValueError("MyMemory returned an empty translation")
                except Exception as fallback_exc:
                    english = (
                        f"(translation unavailable: Google: {google_exc}; "
                        f"MyMemory: {fallback_exc})"
                    )
            if english and not english.startswith("(translation unavailable:"):
                cache[original] = english
                new_translations += 1
                if new_translations % 20 == 0:
                    save_cache(cache)

        word_lines = "\n".join(breakdown(visible, tagger, converter, dictionary))
        sections.append(
            f"## {number} — {timestamp}\n"
            f"**Japanese:** {visible}  \n"
            f"**Romaji:** {romanize(visible, converter)}  \n"
            f"**English:** {english}  \n\n"
            f"**Word breakdown:**\n{word_lines}"
        )

    save_cache(cache)
    title = f"# One Punch Man S01E{episode:02d} — Complete Study Notes"
    output.write_text(title + "\n\n" + "\n\n".join(sections) + "\n", encoding="utf-8")
    print(f"Wrote {len(sections)} sections to {output}")


if __name__ == "__main__":
    main()
