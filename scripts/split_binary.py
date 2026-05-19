#!/usr/bin/env python3
"""
Utiliza los archivos separados por categoría para creae 2 carpetas con separación control vs experimental
  control/      ← TD 
  experimental/ ← DS + HL + LT + SLI
Se limpia la carpeta de categorized_bi si hay datos adentro

"""

import shutil
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────────

BASE    = Path("/Tu/propio/path")
SRC     = BASE / "categorized"
DST     = BASE / "categorized_bi"

CONTROL      = {"TD"}
EXPERIMENTAL = {"DS", "HL", "LT", "SLI"}

GROUP_MAP = {
    **{cat: "control"      for cat in CONTROL},
    **{cat: "experimental" for cat in EXPERIMENTAL},
}

# ── Setup ──────────────────────────────────────────────────────────────────────
# Crealas carpetas necesarias
if DST.exists():
    shutil.rmtree(DST)

(DST / "control").mkdir(parents=True)
(DST / "experimental").mkdir(parents=True)

# ── Copy files ─────────────────────────────────────────────────────────────────
# Copia los archivos en su respectivo grupo
counts = {"control": 0, "experimental": 0}

for cat, group in GROUP_MAP.items():
    src_dir = SRC / cat
    if not src_dir.exists():
        print(f"  Warning: {src_dir} not found, skipping.")
        continue

    cha_files = sorted(src_dir.glob("*.cha"))
    print(f"[{cat}] {len(cha_files)} files → {group}/")

    for src_file in cha_files:
        shutil.copy2(src_file, DST / group / src_file.name)
        counts[group] += 1

# ── Metadata ───────────────────────────────────────────────────────────────────

def avg_lines(directory: Path) -> float:
    files = list(directory.glob("*.cha"))
    if not files:
        return 0.0
    total = 0
    for f in files:
        try:
            with open(f, encoding="utf-8", errors="replace") as fh:
                total += sum(1 for _ in fh)
        except OSError:
            pass
    return total / len(files)

print("\ metadata...")

ctrl_avg = avg_lines(DST / "control")
exp_avg  = avg_lines(DST / "experimental")

with open(DST / "global_metadata.txt", "w", encoding="utf-8") as f:
    f.write("Categorized-Bi Summary\n")
    f.write("=" * 50 + "\n\n")
    f.write(f"control (TD):\n")
    f.write(f"  Files        : {counts['control']}\n")
    f.write(f"  Average lines: {ctrl_avg:.1f}\n\n")
    f.write(f"experimental (DS + HL + LT + SLI):\n")
    f.write(f"  Files        : {counts['experimental']}\n")
    f.write(f"  Average lines: {exp_avg:.1f}\n\n")
    f.write(f"Grand total    : {counts['control'] + counts['experimental']}\n")
