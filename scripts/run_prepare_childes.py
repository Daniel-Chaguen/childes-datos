#!/usr/bin/env python3
"""
run_prepare_childes.py

Batch-runs prepare_childes.py over all .cha files in categorized_bi/
(control/ and experimental/) and writes cleaned output to prepared_bi/.

Changes vs original version:
  - Default config is now classifier.yaml (optimised for classification).
  - CHI_ONLY = True: output files contain only the target child's utterances.
    The <CHI> speaker tag is stripped since it is redundant when every line
    in the file already belongs to the child.
  - Continuation-line bug in prepare_childes.py has been fixed upstream so
    Forrester files (and any other corpora with tab-indented timing lines)
    no longer crash.

Output structure:
  prepared_bi/
    control/        ← cleaned CHI-only TD utterances (.txt)
    experimental/   ← cleaned CHI-only DS+HL+LT+SLI utterances (.txt)
    errors.log      ← created only if any files fail

Usage:
    python3 run_prepare_childes.py [--config path/to/config.yaml] [--no-chi-only]
"""

import argparse
import re
import sys
import shutil
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────────

BASE        = Path("/home/danielch/Desktop/progra_2026pt1/analisis/final/proyecto_final")
PYCHILDES   = BASE / "PyChildes"
SRC_ROOT    = BASE / "categorized_bi"
DST_ROOT    = BASE / "prepared_bi"
DEFAULT_CFG = str(PYCHILDES / "configs" / "classifier.yaml")

OUTPUT_EXT  = ".txt"   # change to ".jsonl" or ".json" if preferred

# Make PyChildes importable (its modules use plain relative imports)
sys.path.insert(0, str(PYCHILDES))
from prepare_childes import process_cha_file  # noqa: E402

# ── CHI-only filter ────────────────────────────────────────────────────────────

def filter_chi_only(file_path: Path) -> int:
    """
    Keep only lines spoken by the target child (starting with '<CHI>'),
    strip the '<CHI>' speaker tag, remove nonverbal <0> tokens (gestures and
    silent turns), and drop lines that carry no linguistic content after cleanup.
    <unk> tokens are kept since their frequency is a diagnostic signal.
    Returns the number of utterances kept.
    """
    with open(file_path, encoding="utf-8") as f:
        lines = f.readlines()

    chi_lines = []
    for line in lines:
        stripped = line.strip()
        if not stripped.startswith('<CHI>'):
            continue

        # Remove the speaker tag: "<CHI> text ." → "text ."
        content = stripped[len('<CHI>'):].lstrip()

        # Remove nonverbal <0> tokens (gestures, silent turns, &=events).
        # These carry no speech signal for a text classifier.
        content = re.sub(r'<0>\s*', '', content)

        # Collapse extra whitespace left by removal
        content = re.sub(r' {2,}', ' ', content).strip()

        # Drop lines that are empty or reduced to bare punctuation
        if content and not re.fullmatch(r'[.!?,;:]+', content):
            chi_lines.append(content + '\n')

    with open(file_path, 'w', encoding="utf-8") as f:
        f.writelines(chi_lines)

    return len(chi_lines)

# ── Batch runner ───────────────────────────────────────────────────────────────

def run_batch(config_path: str, chi_only: bool) -> None:
    groups = ["control", "experimental"]
    total_ok = total_err = total_empty = 0
    errors: list[tuple[str, str]] = []

    # Clear previous run so stale files don't persist
    if DST_ROOT.exists():
        shutil.rmtree(DST_ROOT)

    for group in groups:
        src_dir = SRC_ROOT / group
        dst_dir = DST_ROOT / group
        dst_dir.mkdir(parents=True, exist_ok=True)

        cha_files = sorted(src_dir.glob("*.cha"))
        print(f"\n[{group}] {len(cha_files)} files → {dst_dir}")

        for idx, src_file in enumerate(cha_files, 1):
            stem     = src_file.stem
            dst_file = dst_dir / (stem + OUTPUT_EXT)

            try:
                process_cha_file(str(src_file), str(dst_file), config_path)

                if chi_only:
                    n_kept = filter_chi_only(dst_file)
                    # Remove files where the child produced nothing
                    if n_kept == 0:
                        dst_file.unlink()
                        total_empty += 1
                        continue

                total_ok += 1

            except Exception as exc:
                total_err += 1
                errors.append((str(src_file), str(exc)))

            if idx % 500 == 0 or idx == len(cha_files):
                print(f"  {idx}/{len(cha_files)}  "
                      f"(ok={total_ok}  empty={total_empty}  err={total_err})",
                      flush=True)

    # ── Summary ────────────────────────────────────────────────────────────────
    print(f"\nDone.")
    print(f"  Processed successfully : {total_ok}")
    print(f"  Skipped (no CHI speech): {total_empty}")
    print(f"  Errors                 : {total_err}")
    print(f"  Output                 : {DST_ROOT}")

    if errors:
        err_log = DST_ROOT / "errors.log"
        with open(err_log, "w", encoding="utf-8") as f:
            for path, msg in errors:
                f.write(f"{path}\n  {msg}\n\n")
        print(f"  Error log              : {err_log}")


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Batch-prepare all categorized_bi .cha files with prepare_childes."
    )
    parser.add_argument(
        "--config",
        type=str,
        default=DEFAULT_CFG,
        help=f"Path to YAML config (default: classifier.yaml)",
    )
    parser.add_argument(
        "--no-chi-only",
        action="store_true",
        default=False,
        help="Keep all speakers instead of filtering to CHI only (default: CHI only)",
    )
    args = parser.parse_args()

    chi_only = not args.no_chi_only

    print(f"Config   : {args.config}")
    print(f"Source   : {SRC_ROOT}")
    print(f"Output   : {DST_ROOT}")
    print(f"Format   : {OUTPUT_EXT}")
    print(f"CHI only : {chi_only}")
    run_batch(args.config, chi_only)
