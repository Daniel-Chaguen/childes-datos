#!/usr/bin/env python3
"""
run_prepare_childes.py

Preprocesa los archivos .cha en la carpeta de categorized_bi.

Changes vs original version:
  - classifier.yaml (optimised for classification).
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

BASE        = Path("/Tu/propio/path")
PYCHILDES   = BASE / "PyChildes"
SRC_ROOT    = BASE / "categorized_bi"
DST_ROOT    = BASE / "prepared_bi"
# Identificamos el path hacia el archivo yaml con la configuración
DEFAULT_CFG = str(PYCHILDES / "configs" / "classifier.yaml")

# Determina el formato en txt, se puede cambiar si es necesario
OUTPUT_EXT  = ".txt" 

# Llama la función desde el código orignal del repositorio
sys.path.insert(0, str(PYCHILDES))
from prepare_childes import process_cha_file  # noqa: E402

# ── CHI-only filter ────────────────────────────────────────────────────────────

def filter_chi_only(file_path: Path) -> int:
    """
    Filtra las líneas para quedarse sólo con las líneas que empiezan con <CHI>.
    REmeuve texto no verbal y <unk> que es resultado de palabras o señales no identificadas.
    Limpia líneas que no tienen contenido linguístico.
    """
    with open(file_path, encoding="utf-8") as f:
        lines = f.readlines()

    chi_lines = []
    for line in lines:
        stripped = line.strip()
        if not stripped.startswith('<CHI>'):
            continue

        # Quita <CHI>
        content = stripped[len('<CHI>'):].lstrip()

        #  Quita <0>
        content = re.sub(r'<0>\s*', '', content)

        # Quita <unk> 
        content = re.sub(r'<unk>\s*', '', content)

        # Quita espacios extra en blanco
        content = re.sub(r' {2,}', ' ', content).strip()

        #Quita líneas vacías o que solo mantienen signos de puntuación
        if content and not re.fullmatch(r'[.!?,;:]+', content):
            chi_lines.append(content + '\n')

    with open(file_path, 'w', encoding="utf-8") as f:
        f.writelines(chi_lines)

    return len(chi_lines)

# ── Batch runner ───────────────────────────────────────────────────────────────

MIN_LINES = 10

#  "control" → "ctrl", "experimental" → "exp"
GROUP_PREFIX = {"control": "ctrl", "experimental": "exp"}


def run_batch(config_path: str, chi_only: bool) -> None:
    groups = ["control", "experimental"]
    total_ok = total_err = total_empty = total_short = 0
    errors: list[tuple[str, str]] = []

    # Limpia los restos de archivos antes procesados
    if DST_ROOT.exists():
        shutil.rmtree(DST_ROOT)

    for group in groups:
        src_dir  = SRC_ROOT / group
        dst_dir  = DST_ROOT / group
        dst_dir.mkdir(parents=True, exist_ok=True)

        prefix     = GROUP_PREFIX[group]
        cha_files  = sorted(src_dir.glob("*.cha"))
        file_id    = 0   # counter for the clean sequential ID

        print(f"\n[{group}] {len(cha_files)} files → {dst_dir}")

        for idx, src_file in enumerate(cha_files, 1):
            tmp_file = dst_dir / (src_file.stem + OUTPUT_EXT)

            try:
                process_cha_file(str(src_file), str(tmp_file), config_path)

                if chi_only:
                    n_kept = filter_chi_only(tmp_file)
                    if n_kept == 0:
                        tmp_file.unlink()
                        total_empty += 1
                        continue
                    if n_kept < MIN_LINES:
                        tmp_file.unlink()
                        total_short += 1
                        continue

                file_id += 1
                final_file = dst_dir / f"{prefix}_{file_id:05d}{OUTPUT_EXT}"
                tmp_file.rename(final_file)
                total_ok += 1

            except Exception as exc:
                total_err += 1
                errors.append((str(src_file), str(exc)))
                if tmp_file.exists():
                    tmp_file.unlink()

            if idx % 500 == 0 or idx == len(cha_files):
                print(f"  {idx}/{len(cha_files)}  "
                      f"(ok={total_ok}  short={total_short}  "
                      f"empty={total_empty}  err={total_err})",
                      flush=True)

    # ── Summary ────────────────────────────────────────────────────────────────
    print(f"\nDone.")
    print(f"  Processed successfully : {total_ok}")
    print(f"  Skipped (no CHI speech): {total_empty}")
    print(f"  Skipped (< {MIN_LINES} lines)  : {total_short}")
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
