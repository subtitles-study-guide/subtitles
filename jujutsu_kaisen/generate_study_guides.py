#!/usr/bin/env python3
"""Generate a complete Jujutsu Kaisen Season 1 Japanese study guide."""

from __future__ import annotations

import json
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
CACHE = REPO_ROOT / "shared_translation_cache.json"

GLOSSES = {
    "は": "topic marker", "が": "subject marker", "を": "object marker",
    "に": "to / at / in", "で": "at / by / with", "と": "and / with / quotation marker",
    "の": "possessive / linking particle", "も": "also", "へ": "toward",
    "から": "from / because", "まで": "until", "より": "than", "か": "question marker",
    "ね": "right? / sentence-ending particle", "よ": "emphasis / notification",
    "って": "quotation / colloquial topic marker", "けど": "but / though",
    "です": "is / polite copula", "だ": "is / plain copula", "ない": "not / nonexistent",
    "する": "to do", "いる": "to be / exist (animate)", "ある": "to be / exist",
    "これ": "this", "それ": "that", "あれ": "that / huh?", "どこ": "where",
    "何": "what", "誰": "who", "どう": "how", "今": "now", "人": "person / people",
    "君": "you", "私": "I / me", "僕": "I (male)", "俺": "I (casual male)",
    "おはよう": "good morning / morning", "はい": "yes", "もう": "already / now",
    "まだ": "still / not yet", "本当": "truth / really", "大丈夫": "okay / all right",
}

NAMES = {
    "五条": "Gojo", "悟": "Satoru", "虎杖": "Itadori", "悠仁": "Yuji",
    "伏黒": "Fushiguro", "恵": "Megumi", "釘崎": "Kugisaki", "野薔薇": "Nobara",
    "宿儺": "Sukuna", "両面宿儺": "Ryomen Sukuna", "杉沢": "Sugisawa",
    "佐々木": "Sasaki", "井口": "Iguchi",
}

TRANSLATION_OVERRIDES = {
    # Lines that the public translators consistently reject (Episodes 4-6).
    "まあ元来 呪霊は 生まれた場に とどまるものだしな":
        "Well, cursed spirits generally remain in the place where they were born.",
    "ここで―": "Here—",
    "ガハッ アア": "Gah! Aah!",
    "（宿儺）おい どうした？": "(Sukuna) Hey, what's wrong?",
    "（宿儺）呪霊といえど―": "(Sukuna) Even if it is a cursed spirit—",
    "腕は惜しいか？": "Do you hate to lose your arm?",
    "（伏黒）避難区域 10キロまで広げてください":
        "(Fushiguro) Please expand the evacuation zone to ten kilometers.",
    "そうですか 私も 釘崎さんを病院へ届けたら―":
        "I see. Once I've taken Ms. Kugisaki to the hospital—",
    "まあ いないと思うけど": "Well, I don't think there are any.",
    "（伏黒）あいつが もしもの時は": "(Fushiguro) If anything happens to him...",
    "少しでも多くの善人が 平等を享受できるように…":
        "So that as many good people as possible can enjoy fairness...",
    "俺は不平等に人を助ける": "I save people unequally.",
    "いい いいぞ": "Good. Very good.",
    "お前が命を燃やすのは これからだったわけだ":
        "So you were only just about to start putting your life on the line.",
    "そうか それなら…": "I see. In that case...",
    "魅せてみろ 伏黒 恵！": "Show me what you've got, Megumi Fushiguro!",
    "布瑠部 由良由良 やつ… あ…": "With this treasure, I summon... ah...",
    "言っておくが俺は―": "Let me make this clear—",
    "お前を助けた理由に 論理的な思考を持ち合わせていない":
        "There was no logical reasoning behind why I saved you.",
    "危険だとしても お前のような善人が死ぬのを―":
        "Even if it was dangerous, I didn't want to see a good person like you—",
    "見たくなかった": "die.",
    "それなりに迷いはしたが―": "I did hesitate in my own way, but—",
    "結局は わがままな感情論": "In the end, it was selfish, emotional reasoning.",
    "でも それでいいんだ": "But that's all right.",
    "俺はヒーローじゃない": "I'm not a hero.",
    "呪術師なんだ": "I'm a jujutsu sorcerer.",
    "だから お前を助けたことを―": "That's why saving you—",
    "一度だって後悔したことはない": "is something I've never regretted, not even once.",
    "（虎杖）そっか": "(Itadori) I see.",
    "俺より いろいろ考えてんだろ": "You've thought about a lot more than I have.",
    "お前の真実は正しいと思う": "I think your convictions are right.",
    "長生きしろよ": "Live a long life.",
    "くっ うっ うう…": "Guh... ugh...",
    "わざわざ貴重な指１本使ってまで 確かめる必要があったかね":
        "Did you really need to use one precious finger just to confirm that?",
    "（夏油）まあ 中途半端な 当て馬じゃ 意味ないからね":
        "(Geto) Well, using a half-baked sacrificial pawn would have been pointless.",
    "物を出し入れできる呪霊を飼ってる 術師とかもいるよな":
        "There are sorcerers who keep cursed spirits that can store and retrieve objects, right?",
    "見つけたら 私に教えろよ": "If you find one, let me know.",
    "（東堂）同じことだ 帰れ！": "(Todo) Same thing. Go home!",
    "（桃）呪霊狩りも 私が空から 索敵しないと始まんないよね":
        "(Momo) We can't even start hunting cursed spirits unless I scout from the air, right?",
    "（メカ丸）御意 （真依）まあ―": "(Mechamaru) As you command. (Mai) Well—",
    "あの人いないと困るしね": "We'd be in trouble without her, too.",
    "ありえるな": "That's possible.",
    "確かに そこまでの敵意は 感じなかったが―":
        "It's true that I didn't sense that much hostility, but—",
    "俺たちも さっき分かった ありゃ 善人":
        "We only realized it earlier ourselves. That guy's a good person.",
    "（真希）戻るぞ 恵": "(Maki) We're heading back, Megumi.",
    "（パンダ）俺と野薔薇は 戻って 悠仁の安否を確認する":
        "(Panda) Nobara and I will go back and make sure Yuji is safe.",
}


def parse_srt(path: Path) -> list[tuple[int, str, str]]:
    blocks = []
    for raw in re.split(r"\n\s*\n", path.read_text(encoding="utf-8").strip()):
        lines = [line.strip() for line in raw.splitlines() if line.strip()]
        if len(lines) < 3 or "-->" not in lines[1]:
            continue
        try:
            number = int(lines[0].lstrip("\ufeff"))
        except ValueError:
            continue
        blocks.append((number, lines[1], " ".join(lines[2:])))
    return blocks


def display_text(text: str) -> str:
    # Netflix CC sometimes places a kana reading after a speaker's kanji name.
    return re.sub(r"([一-龯々]+)\([ぁ-ゖァ-ヺー]+\)", r"\1", text)


def romanize(text: str, converter: object) -> str:
    value = " ".join(item["hepburn"] for item in converter.convert(display_text(text)))
    value = value.replace("（", "(").replace("）", ")")
    return re.sub(r"\s+", " ", value).strip()


def feature_value(feature: object, *names: str) -> str:
    for name in names:
        value = getattr(feature, name, None)
        if value and value != "*":
            return str(value)
    return ""


def dictionary_meaning(surface: str, lemma: str, dictionary: Jamdict) -> str:
    if surface in NAMES:
        return NAMES[surface]
    if surface in GLOSSES:
        return GLOSSES[surface]
    if lemma in GLOSSES:
        return GLOSSES[lemma]

    # Inflected verbs and adjectives are usually found under their UniDic lemma.
    for query in dict.fromkeys((lemma, surface)):
        if not query:
            continue
        result = dictionary.lookup(query)
        if not result.entries:
            continue
        for entry in result.entries[:3]:
            for sense in entry.senses:
                glosses = [gloss.text for gloss in sense.gloss if gloss.lang in ("", "eng")]
                if glosses:
                    return " / ".join(glosses[:3])
    return "meaning not found in JMdict"


def breakdown(
    text: str, tagger: fugashi.Tagger, converter: object, dictionary: Jamdict
) -> list[str]:
    visible = display_text(text)
    if "♪" in visible:
        return ["- ♪ — music cue"]

    result = []
    for token in tagger(visible):
        surface = token.surface.strip()
        if not surface or re.fullmatch(r"[（）()！？!?。、…～~・]+", surface):
            continue
        lemma = feature_value(token.feature, "lemma", "orthBase")
        meaning = dictionary_meaning(surface, lemma, dictionary)
        reading = romanize(surface, converter)
        result.append(f"- {surface} ({reading}) — {meaning}")
    return result or [f"- {visible} ({romanize(visible, converter)}) — expression"]


def polished_prefix(path: Path) -> dict[int, str]:
    """Read the hand-edited first 25 sections already in the sample file."""
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    matches = list(re.finditer(r"(?m)^## (\d+) — .+$", text))
    sections = {}
    for index, match in enumerate(matches):
        number = int(match.group(1))
        if number > 25:
            break
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        sections[number] = text[match.start():end].strip()
    return sections


def legacy_translations(source: Path) -> dict[str, str]:
    """Load successful translations from the older study guide, when present."""
    path = source.with_name(source.stem + "_study.md")
    if not path.exists():
        return {}
    translations = {}
    for block in re.split(r"(?m)(?=^## \d+ — )", path.read_text(encoding="utf-8")):
        japanese = re.search(r"(?m)^Japanese: (.+)$", block)
        english = re.search(r"(?m)^English: (.+)$", block)
        if japanese and english and "translation failed" not in english.group(1):
            translations[japanese.group(1).strip()] = english.group(1).strip()
    return translations


def main() -> None:
    episode = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    if not 1 <= episode <= 99:
        raise SystemExit("Episode must be between 1 and 99")
    episode_code = f"{episode:02d}"
    source = ANIME_DIR / "captions" / f"episode_{episode_code}.ja.srt"
    output = OUTPUT_DIR / f"jujutsu_s01e{episode_code}_complete_study_better.md"
    if not source.exists():
        raise SystemExit(f"Subtitle not found: {source}")

    cache = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}
    legacy_cache = legacy_translations(source)
    retained = {}
    converter = kakasi()
    tagger = fugashi.Tagger()
    dictionary = Jamdict()
    translator = GoogleTranslator(source="ja", target="en")
    fallback_translator = MyMemoryTranslator(source="japanese", target="english")

    sections = []
    changed_cache = False
    for number, timestamp, original in parse_srt(source):
        if number in retained:
            sections.append(retained[number])
            continue

        visible = display_text(original)
        if "♪" in visible:
            english = "♪"
            reading = "—"
        else:
            english = (
                cache.get(original.strip())
                or legacy_cache.get(original.strip())
                or TRANSLATION_OVERRIDES.get(visible)
            )
            if not english:
                try:
                    time.sleep(0.3)
                    english = translator.translate(original)
                    cache[original.strip()] = english
                    changed_cache = True
                except Exception as google_exc:
                    try:
                        english = fallback_translator.translate(original)
                        cache[original.strip()] = english
                        changed_cache = True
                    except Exception as fallback_exc:
                        english = (
                            f"(translation unavailable: Google: {google_exc}; "
                            f"MyMemory: {fallback_exc})"
                        )
            reading = romanize(visible, converter)

        word_lines = "\n".join(breakdown(visible, tagger, converter, dictionary))
        sections.append(
            f"## {number} — {timestamp}\n"
            f"**Japanese:** {visible}  \n"
            f"**Romaji:** {reading}  \n"
            f"**English:** {english}  \n\n"
            f"**Word breakdown:**\n{word_lines}"
        )

    title = f"# Jujutsu Kaisen S01E{episode_code} — Complete Study Notes"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output.write_text(title + "\n\n" + "\n\n".join(sections) + "\n", encoding="utf-8")
    if changed_cache:
        CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(sections)} sections to {output}")


if __name__ == "__main__":
    main()
