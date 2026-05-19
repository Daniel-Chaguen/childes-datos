#!/usr/bin/env python3
"""
categorize_cha.py

Categorizes CHILDES .cha files into: DS, TD, SLI, LT, HL.

Detection logic (applied together; conflicts go to 'unsure/'):
  1. Path-based  : if any ancestor directory is named exactly after a category
  2. @Types line : e.g.  @Types:  cross, toyplay, LT
  3. @ID line    : the 2nd pipe-delimited field, e.g.  @ID: eng|DS|CHI|...

Outputs
-------
  categorized/
    DS/
      <prefixed>.cha files
      metadata.txt          ← line count per file
    TD/ SLI/ LT/ HL/ (same structure)
    unsure/
      <prefixed>.cha files
      metadata.txt          ← filename + reason for each file
    global_metadata.txt     ← file count & avg line count per category
"""

import re
import shutil
import sys
from collections import defaultdict
from pathlib import Path

# ── Configuration ──────────────────────────────────────────────────────────────

CATEGORIES: set[str] = {"DS", "TD", "SLI", "LT", "HL"}

SRC = Path(
    "/home/danielch/Desktop/progra_2026pt1/analisis/final/proyecto_final/raw/childes"
)
DST = Path(
    "/home/danielch/Desktop/progra_2026pt1/analisis/final/proyecto_final/categorized"
)

# ── Helpers ────────────────────────────────────────────────────────────────────

def categories_from_path(file_path: Path) -> set[str]:
    """Return any category names found among ancestor directory components."""
    try:
        rel = file_path.relative_to(SRC)
    except ValueError:
        return set()
    # rel.parts[-1] is the filename; everything before that are directories
    return {part for part in rel.parts[:-1] if part in CATEGORIES}


def categories_from_content(file_path: Path) -> tuple[set[str], list[str]]:
    """
    Scan the file header for category markers.
    Returns (found_categories, list_of_evidence_strings).
    """
    found: set[str] = set()
    evidence: list[str] = []

    try:
        with open(file_path, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.rstrip()

                # @Types:  cross, toyplay, LT
                if line.startswith("@Types:"):
                    tokens = re.split(r"[\s,\t]+", line)
                    for tok in tokens:
                        if tok in CATEGORIES:
                            found.add(tok)
                            evidence.append(f'@Types token "{tok}"')

                # @ID:  eng|DS|CHI|9;11.|female|||Target_Child|||
                # 2nd pipe-delimited field (index 1) is the corpus name
                elif line.startswith("@ID:"):
                    m = re.match(r"@ID:\s+\w+\|([^|]+)\|", line)
                    if m:
                        corpus = m.group(1)
                        if corpus in CATEGORIES:
                            found.add(corpus)
                            evidence.append(f'@ID corpus field "|{corpus}|"')
    except OSError as exc:
        evidence.append(f"read error: {exc}")

    return found, evidence


def dest_filename(file_path: Path) -> str:
    """
    Build a flat destination filename by joining all relative path components
    with underscores.
    e.g.  Eng-NA/Brown/Sarah/040700.cha  →  Eng-NA_Brown_Sarah_040700.cha
    """
    rel = file_path.relative_to(SRC)
    return "_".join(rel.parts)


def line_count(file_path: Path) -> int:
    try:
        with open(file_path, encoding="utf-8", errors="replace") as fh:
            return sum(1 for _ in fh)
    except OSError:
        return 0


# ── Setup output directories ───────────────────────────────────────────────────

for folder in list(CATEGORIES) + ["unsure"]:
    (DST / folder).mkdir(parents=True, exist_ok=True)

# ── Main processing loop ───────────────────────────────────────────────────────

# cat_records[cat] = list of (dest_filename, line_count)
cat_records: dict[str, list[tuple[str, int]]] = defaultdict(list)
# unsure_records = list of (dest_filename, reason_string)
unsure_records: list[tuple[str, str]] = []

all_cha = sorted(SRC.rglob("*.cha"))
total = len(all_cha)
print(f"Found {total} .cha files. Processing...")

for idx, fpath in enumerate(all_cha, 1):
    if idx % 500 == 0 or idx == total:
        print(f"  {idx}/{total}", flush=True)

    path_cats = categories_from_path(fpath)
    content_cats, evidence = categories_from_content(fpath)
    all_cats = path_cats | content_cats
    dname = dest_filename(fpath)

    if len(all_cats) == 0:
        reason = "no category marker found in path or file content"
        unsure_records.append((dname, reason))
        shutil.copy2(fpath, DST / "unsure" / dname)

    elif len(all_cats) == 1:
        cat = next(iter(all_cats))
        lc = line_count(fpath)
        shutil.copy2(fpath, DST / cat / dname)
        cat_records[cat].append((dname, lc))

    else:
        # Multiple different categories detected — cannot assign unambiguously
        path_str = ", ".join(sorted(path_cats)) if path_cats else "none"
        cont_str  = ", ".join(sorted(content_cats)) if content_cats else "none"
        ev_str    = "; ".join(evidence) if evidence else "none"
        reason = (
            f"multiple categories detected: {', '.join(sorted(all_cats))} "
            f"(from path: [{path_str}]; from content: [{cont_str}] via [{ev_str}])"
        )
        unsure_records.append((dname, reason))
        shutil.copy2(fpath, DST / "unsure" / dname)

print("Copying done. Writing metadata...")

# ── Per-category metadata ──────────────────────────────────────────────────────

for cat in sorted(CATEGORIES):
    records = sorted(cat_records.get(cat, []))
    meta_path = DST / cat / "metadata.txt"
    with open(meta_path, "w", encoding="utf-8") as f:
        f.write(f"Category : {cat}\n")
        f.write(f"Files    : {len(records)}\n")
        avg = sum(lc for _, lc in records) / len(records) if records else 0.0
        f.write(f"Avg lines: {avg:.1f}\n")
        f.write("\n")
        f.write(f"{'Filename':<80}  {'Lines':>6}\n")
        f.write("-" * 88 + "\n")
        for fname, lc in records:
            f.write(f"{fname:<80}  {lc:>6}\n")

# ── Unsure metadata ────────────────────────────────────────────────────────────

unsure_meta = DST / "unsure" / "metadata.txt"
with open(unsure_meta, "w", encoding="utf-8") as f:
    f.write(f"Unsure files: {len(unsure_records)}\n")
    f.write("=" * 60 + "\n\n")
    for fname, reason in sorted(unsure_records):
        f.write(f"File  : {fname}\n")
        f.write(f"Reason: {reason}\n")
        f.write("\n")

# ── Global metadata ────────────────────────────────────────────────────────────

global_meta = DST / "global_metadata.txt"
with open(global_meta, "w", encoding="utf-8") as f:
    f.write("Global Category Summary\n")
    f.write("=" * 50 + "\n\n")
    grand_total = 0
    for cat in sorted(CATEGORIES):
        records = cat_records.get(cat, [])
        count = len(records)
        grand_total += count
        avg = sum(lc for _, lc in records) / count if count else 0.0
        f.write(f"{cat}:\n")
        f.write(f"  Files        : {count}\n")
        f.write(f"  Average lines: {avg:.1f}\n\n")
    unsure_count = len(unsure_records)
    f.write(f"unsure:\n")
    f.write(f"  Files        : {unsure_count}\n\n")
    f.write(f"Total classified : {grand_total}\n")
    f.write(f"Total unclassified: {unsure_count}\n")
    f.write(f"Grand total      : {grand_total + unsure_count}\n")

print(f"\nDone.")
print(f"Output: {DST}")
print(f"\nQuick summary:")
for cat in sorted(CATEGORIES):
    print(f"  {cat:5s}: {len(cat_records.get(cat, []))} files")
print(f"  unsure: {len(unsure_records)} files")
