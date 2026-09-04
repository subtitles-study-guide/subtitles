# Japanese Subtitle Study Guides

This repository contains Japanese caption files, generated study guides, and
the Python scripts used to build them for:

- Jujutsu Kaisen, Season 1 (Episodes 1-24)
- One Punch Man, Season 1 (Episodes 1-12)

Each guide includes the original Japanese caption, romanization, an English
translation, and a Japanese-English vocabulary breakdown.

## Caption sources

The Jujutsu Kaisen Season 1 Japanese captions were obtained from the
[Kitsunekko Japanese subtitle directory](https://kitsunekko.net/dirlist.php?dir=subtitles%2Fjapanese%2F).

The One Punch Man Season 1 Japanese captions were extracted from Netflix with
the [Subadub Chrome extension](https://chromewebstore.google.com/detail/subadub/jamiekdimmhnnemaaimmdahnahfmfdfk).
Access to the Japanese captions required using a VPN with the location set to
Japan.

Because the two shows use captions from different sources, formatting, timing,
speaker labels, and transcription quality may vary. The captions are correct
for the most part, but occasional mistakes or inconsistencies may remain.

You can use the Subadub method to obtain captions for other shows manually when
they are available through your streaming region. Another option is to search
for Japanese subtitle files online, although availability and quality vary
considerably.

## Layout

```text
jujutsu_kaisen/
  captions/
  study_guides/
  generate_study_guides.py
one_punch_man/
  captions/
  study_guides/
  generate_study_guides.py
shared_translation_cache.json
```

The generators share `shared_translation_cache.json`, allowing exact
Japanese captions already translated for one show to be reused by the other.

## Setup

Use Python 3.10 or newer and install the dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

No API keys are required. The scripts use `deep-translator` with Google
Translate and MyMemory as public translation providers when a caption is not
already cached.

## Generate a guide

Run commands from the repository root:

```bash
python3 jujutsu_kaisen/generate_study_guides.py 1
python3 one_punch_man/generate_study_guides.py 1
```

Replace `1` with the desired Season 1 episode number. Results are written to
the matching anime's `study_guides/` folder.

For example, to generate Jujutsu Kaisen Episode 8:

```bash
python3 jujutsu_kaisen/generate_study_guides.py 8
```

To generate One Punch Man Episode 8:

```bash
python3 one_punch_man/generate_study_guides.py 8
```

The corresponding Japanese SRT must be present in that anime's `captions/`
folder and named `episode_08.ja.srt`.

## Using ChatGPT or another LLM

If you use ChatGPT Codex or another coding assistant with access to a local
terminal, it may be easier to ask it to install the requirements and run the
generator for you. Open the repository as its workspace and use a prompt such
as:

> Install the Python dependencies from `requirements.txt`, then run the One
> Punch Man study-guide generator for Episode 8. Keep all generated output in
> the existing `study_guides` folder and report any failed translations.

For multiple episodes, ask it to process a specific range and verify every
result afterward. Translation providers may be slow or temporarily reject
requests, so instructing the assistant to preserve and reuse the shared cache
will prevent completed translations from being repeated.

A browser-only LLM chat generally cannot run scripts against files on your
computer. In that case, you can upload an SRT and ask the model to create a
study guide directly, but long episodes may exceed file or response limits.
Using a coding assistant with repository and terminal access is more reliable
for full seasons.

## Notes

- Translation services can throttle or reject requests. Successful responses
  are retained in the shared cache.
- Vocabulary definitions come from JMdict. Proper names, sound effects, and
  fragmented expressions may not have dictionary entries.
- Review the licensing and redistribution status of caption and dialogue
  content before publishing or redistributing this repository.
