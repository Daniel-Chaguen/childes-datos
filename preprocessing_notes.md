# CHILDES Preprocessing Pipeline
**Project:** Language disorder classification — TD vs DS / HL / LT / SLI  
**Author:** Daniel CH  
**Last updated:** 2026-05-19

---

## Overview

The goal is to turn raw CHILDES transcripts into clean, classifier-ready text files containing only what the target child said. The pipeline has four stages:

```
raw/childes/          →  categorized/       →  categorized_bi/       →  prepared_bi/
14,530 .cha files        sorted by group       binary split              cleaned .txt files
```

---

## Stage 1 — Raw Data

**Source:** `raw/childes/`  
**Format:** CHAT (`.cha`) — the TalkBank standard for child language transcripts

CHAT files have three types of lines:
- `@` lines — file headers (participant metadata, date, language, corpus)
- `*` lines — speaker utterances: `*CHI:\t I wanna go .`
- `%` lines — researcher annotations: morphology (`%mor`), grammar (`%gra`), actions (`%act`)

The rich annotation system also embeds markers *inside* utterances to encode disfluencies, errors, unintelligible speech, prosody, and paralinguistic events.

---

## Stage 2 — Categorisation

**Script:** `scripts/categorize_cha.py`  
**Output:** `categorized/` with subdirectories `DS/ TD/ SLI/ LT/ HL/ unsure/`

Each file is assigned to one of five clinical/developmental groups. Detection uses three independent signals checked in combination:

| Signal | Where it looks | Example |
|---|---|---|
| Path-based | Ancestor directory names | `.../Hooshyar/DS/play/p066.cha` → DS |
| `@Types` header | Comma-separated type codes | `@Types: cross, toyplay, LT` → LT |
| `@ID` corpus field | 2nd pipe-delimited field | `@ID: eng\|DS\|CHI\|...` → DS |

**Assignment rules:**
- Exactly one category found across all signals → assigned to that category
- No signal found → `unsure/`
- Signals conflict (e.g. path says DS, `@Types` says TD) → `unsure/` with reason logged

**Why three signals?** Different corpora use different conventions. The Hooshyar corpus uses directory structure; other corpora embed the group in `@Types` or the `@ID` corpus field. Using all three maximises recall without sacrificing precision — conflicts go to `unsure/` rather than making a wrong assignment.

**Output counts:**

| Group | Files |
|---|---|
| TD — Typically Developing | 12,508 |
| SLI — Specific Language Impairment | 882 |
| LT — Late Talker | 515 |
| HL — Hearing Loss | 162 |
| DS — Down Syndrome | 134 |
| unsure | 329 |

Files in `unsure/` mostly belong to groups outside the target categories (ASD, bilingual, AAE, epilepsy). They are excluded from classification.

Each output category gets a `metadata.txt` (filename + line count per file) and there is a shared `global_metadata.txt`.

---

## Stage 3 — Binary Split

**Output:** `categorized_bi/control/` and `categorized_bi/experimental/`

The six groups are collapsed into two for binary classification:

| Split | Groups | Files |
|---|---|---|
| `control/` | TD only | 12,508 |
| `experimental/` | DS + HL + LT + SLI | 1,693 |

**Why binary?** While multi-class classification is possible, a binary control-vs-clinical split is the standard framing in the clinical linguistics literature and produces a cleaner, more interpretable signal. The four experimental groups share common markers (reduced MLU, increased disfluency, more unintelligible speech) that distinguish them from TD as a class.

**Class imbalance:** control : experimental ≈ 7.4 : 1. This must be addressed during model training with class weights, oversampling, or undersampling.

---

## Stage 4 — CHAT Preprocessing

**Script:** `scripts/run_prepare_childes.py`  
**Config:** `PyChildes/configs/classifier.yaml`  
**Library:** `PyChildes/prepare_childes.py`  
**Output:** `prepared_bi/control/` and `prepared_bi/experimental/`

This stage converts each `.cha` file into a plain-text file of cleaned child utterances, one per line.

### 4a. Line-level filtering

Before any cleaning, lines are filtered by type:

| Line type | Decision | Reason |
|---|---|---|
| `@` header lines | **Dropped** | Pure metadata — no speech content |
| `%` dependent tiers | **Dropped** | Researcher annotations, not child speech. `%gra` in particular contains syntactic parse trees that would directly leak diagnostic information |
| `*` utterance lines | **Kept and cleaned** | The actual speech signal |
| Tab-indented / blank lines | **Silently skipped** | Some corpora (e.g. Forrester in ENG-UK) embed pause timings and audio timestamps on standalone tab-indented lines that are not part of any CHAT tier |

### 4b. Utterance cleaning (applied in order)

Each `*` line passes through the following steps:

**Step 1 — Basic prosodic markers** (`process_basic`)  
Removed: ↑↓ tone direction, `:` vowel lengthening, ˈˌ stress marks, ≠ blocking, `(...)` pauses, `^` inter-syllable pause.  
*Why:* These prosodic annotations are sparse across corpora and add noise for text-based classifiers. They do not carry speech content.

**Step 2 — Utterance linkers** (`process_linker`)  
Special terminators are normalised: `+...` trailing off → `...`, `+/.` interrupted → `...`, `+//.` self-interrupted → `...`, `+.` transcription break → `.`  
*Why:* Preserves sentence boundary information in a standard form.

**Step 3 — Incomplete words** (`process_incomplete`)  
Parenthesised missing material is restored: `(a)n(d)` → `and`.  
*Why:* Both TD and clinical children reduce words in casual speech, so incomplete forms are not a reliable disorder marker. Restoring the full form avoids artificially inflating disorder signal.

**Step 4 — Scoped markers** (`process_paralinguistic`)  
These are the most consequential decisions:

| Marker | Default behaviour | Our behaviour | Reason |
|---|---|---|---|
| `[:]` replacement | Keep correction (`gonna` → `going to`) | **Keep original** (`gonna`) | Non-standard forms are a primary diagnostic signal for SLI, DS, LT |
| `[/]` repetition | Delete repeated material | **Keep** (`I I want`) | Repetitions and false starts are established markers of SLI and DS |
| `[=]` explanation | Wrap in `<exp>` tag | **Remove** | Researcher annotation, not speech |
| `[^]` paralinguistic | Wrap in `<EVT>` tag | **Remove** | Researcher annotation, not speech |
| `[*]` error mark | Remove utterance | Keep utterance | Errors *are* the signal |

**Step 5 — Special form markers** (`process_special_form`)  
Words tagged with `@`-markers are handled based on informativeness:

| Marker | Meaning | Treatment |
|---|---|---|
| `@b` babbling | Pre-linguistic vocalisation | → `<unk>` |
| `@c` child-invented | Made-up word | → `<unk>` |
| `@f` family-specific | Family word | → `<unk>` |
| `@wp` word play | Playful non-word | → `<unk>` |
| `@p` PCF | Phonologically consistent form | → `<unk>` |
| `@fp` filled pause | Annotated uh/um | Removed (inconsistently annotated across corpora) |
| `@d` dialect | Dialectal form | Kept as-is |
| `@i` interjection | oh, ah, wow | Kept as-is |
| `@o` onomatopoeia | moo, woof | Kept as-is |
| `@l` letter | Single letter | Uppercased |
| `@k` multi-letter | String of letters | Uppercased, space-separated |

**Step 6 — Nonverbal marker**  
`0` (action without speech) → `<0>` token.

**Step 7 — Local events**  
`&=laugh`, `&=coughs` etc. → `<0>` (since the paralinguistic wrapper is disabled).

**Step 8 — Disfluencies** (`process_disfluencies`)

| Marker | Meaning | Treatment | Reason |
|---|---|---|---|
| `&+` | Phonological fragment | Removed | Common in TD casual speech; marginal classifier signal |
| `&-` | Filler (uh, um, er) | **Kept** | Well-established prosodic disorder marker |
| `&~` | Nonword | → `<unk>` | No standard lexical content |

**Step 9 — Unidentifiable speech** (`process_unidentifiable`)  
`xxx` (unintelligible), `yyy` (phonologically coded), `www` (untranscribed) → all → `<unk>`.  
*Why:* The frequency of unintelligible speech is a strong diagnostic signal — clinical groups produce systematically more.

### 4c. CHI-only filter and final cleaning (`filter_chi_only`)

After `process_cha_file()` runs, a second pass over the output file:

1. **Keep only `<CHI>` lines** — drops MOT (mother), INV (investigator), FAT (father), SIB (sibling), CLI (clinician), and all other speakers. Adult speech does not carry the diagnostic signal; caregivers speak similarly regardless of the child's diagnosis.
2. **Strip `<CHI>` speaker tag** — redundant since every remaining line belongs to the child.
3. **Remove `<0>` tokens** — gesture and silent turns carry no text signal.
4. **Remove `<unk>` tokens** — after keeping them through processing (where their presence influenced line-level decisions), they are removed in this final pass. The classifier operates on lexical content only.
5. **Drop empty or punctuation-only lines** — lines that become empty after token removal are discarded.

### 4d. File-level filtering and renaming

After `filter_chi_only()`:
- Files with **0 utterances** → deleted (child produced no speech)
- Files with **fewer than 10 utterances** → deleted (too short for meaningful classification)
- Survivors are renamed to a clean sequential ID:
  - `ctrl_00001.txt`, `ctrl_00002.txt`, … for control
  - `exp_00001.txt`, `exp_00002.txt`, … for experimental

---

## Output Format

```
prepared_bi/
  control/
    ctrl_00001.txt     ← one cleaned child utterance per line, UTF-8 plain text
    ctrl_00002.txt
    …
  experimental/
    exp_00001.txt
    …
```

Each file contains one utterance per line. Empty lines are not written. No speaker tags, no CHAT markers, no annotation tokens.

---

## Bug Fix Applied to PyChildes

**File:** `PyChildes/prepare_childes.py`, `process_cha_file()` (~line 1079)

The Forrester corpus (ENG-UK) contains standalone tab-indented lines that hold pause timing and audio link data, e.g. `\t(9.8) 1405_10340`. These are non-standard continuation lines not recognised by the CHAT spec. The original code raised `DataIntegrityError` on any line not starting with `@`, `*`, or `%`, causing 35 Forrester files to fail entirely.

**Fix:** Lines starting with `\t` (tab) and blank lines are now silently skipped. All other unrecognised lines still raise `DataIntegrityError`.

---

## Re-running the Pipeline

```bash
# From: proyecto_final/

# Stage 2 — Categorise
python3 ../scripts/categorize_cha.py

# Stage 3 — Binary split (manual: copy DS/HL/LT/SLI → experimental/, TD → control/)

# Stage 4 — Preprocess
python3 ../scripts/run_prepare_childes.py

# Optional flags:
python3 ../scripts/run_prepare_childes.py --no-chi-only         # keep all speakers
python3 ../scripts/run_prepare_childes.py --config path/to.yaml  # use different config
```

> **Note:** Each run of `run_prepare_childes.py` wipes and rebuilds `prepared_bi/` from scratch.

---

## File Counts Summary

| Stage | Control | Experimental |
|---|---|---|
| After categorisation | 12,508 | 1,693 |
| After preprocessing (≥10 lines, CHI speech present) | ~9,069 | ~1,498 |

The reduction from categorised to prepared counts is due to files where the child produced fewer than 10 utterances after filtering (very short sessions, predominantly adult-directed interactions, or files where the child was largely non-verbal).
