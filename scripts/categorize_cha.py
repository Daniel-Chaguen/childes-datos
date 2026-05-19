#!/usr/bin/env python3
"""
categorize_cha.py

Categoriza los archivos .cha en: DS, TD, SLI, LT, HL.

El siguiente código busca caregorizar los archivos basado en los siguientes criterios
  1. Basado en el nombre del directorio: Si los datos originales se encuentran dentro de una carpeta ya con las iniciales, todos los archivos se categorizan bajo este mismo.
  2. @Types: Dentro de los archivos existen headers @Types que describen la conversación. Si estos tienen alguna de las iniciales, se categorizan acorde a ello. 
  3. @ID: Finalmente, en los archivos hay una línea @ID que menciona quien habla y si tiene alguna condición, de aquí también se puede extraer el grupo. 

Outputs
-------
  Organización en carpetas: DS, TD, SLI, LT, HL y unsure
  Dentro de cada carpeta están los archivos con un nuevo nombre que identifica su origen. La carpeta unsure almacena todos los archivos que no se pudieron categorizar.
  Se crean archivos llamados metadata que almacena info de cuantos archivos hay, el promedio de líneas y cuantas líneas tiene cada archivo. 
"""

import re
import shutil
import sys
from collections import defaultdict
from pathlib import Path

# ── Configuration ──────────────────────────────────────────────────────────────
# Identificamos las categorias a las que se puede pertenecer
CATEGORIES: set[str] = {"DS", "TD", "SLI", "LT", "HL"}

# Origen de los datos
SRC = Path(
    "/tu/propio/path/"
)

# Output de los datos
DST = Path(
    "/tu/propio/path/"
)

# ── Helpers ────────────────────────────────────────────────────────────────────

def categories_from_path(file_path: Path) -> set[str]:
    """Busca en los paths disponibles si alguno coincide con el set de nuestras categorías"""
    try:
        # Busca coincidencia
        rel = file_path.relative_to(SRC)
    except ValueError:
        # Evita un error si no la encuentra
        return set()
    # Busca en todo lo que no es el nombre del archivo
    return {part for part in rel.parts[:-1] if part in CATEGORIES}


def categories_from_content(file_path: Path) -> tuple[set[str], list[str]]:
    """
    Busca la categoria en el cabecero del archivo.
    """
    found: set[str] = set()
    evidence: list[str] = []
  # Guarda en evidencia si es que pertenece a más de un grupo
    try:
        with open(file_path, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.rstrip()

                # busca en @types si coincide con alguna de las categorías
                if line.startswith("@Types:"):
                    tokens = re.split(r"[\s,\t]+", line)
                    for tok in tokens:
                        if tok in CATEGORIES:
                            found.add(tok)
                            evidence.append(f'@Types token "{tok}"')

                # En el caso de no estar en @typer bsuca en @ID si es que existe algun valor para categorizar
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
    Utiliza el path para crear el nombre del nuevo archivo que almacene de dónde viene el archuvo.
    e.g.  Eng-NA/Brown/Sarah/040700.cha  →  Eng-NA_Brown_Sarah_040700.cha
    """
    rel = file_path.relative_to(SRC)
    return "_".join(rel.parts)


def line_count(file_path: Path) -> int:
  # FUnción para contar palabras
    try:
        with open(file_path, encoding="utf-8", errors="replace") as fh:
            return sum(1 for _ in fh)
    except OSError:
        return 0


# ── Setup output directories ───────────────────────────────────────────────────

for folder in list(CATEGORIES) + ["unsure"]:
  # Crea los directorios si es necesario
    (DST / folder).mkdir(parents=True, exist_ok=True)

# ── Main processing loop ───────────────────────────────────────────────────────
# Itera sobre las carpetas y busca las coincidencias para poder separar entre los grupos de interés

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
        path_str = ", ".join(sorted(path_cats)) if path_cats else "none"
        cont_str  = ", ".join(sorted(content_cats)) if content_cats else "none"
        ev_str    = "; ".join(evidence) if evidence else "none"
        reason = (
            f"multiple categories detected: {', '.join(sorted(all_cats))} "
            f"(from path: [{path_str}]; from content: [{cont_str}] via [{ev_str}])"
        )
        unsure_records.append((dname, reason))
        shutil.copy2(fpath, DST / "unsure" / dname)

# ── metadata ──────────────────────────────────────────────────────

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

unsure_meta = DST / "unsure" / "metadata.txt"
with open(unsure_meta, "w", encoding="utf-8") as f:
    f.write(f"Unsure files: {len(unsure_records)}\n")
    f.write("=" * 60 + "\n\n")
    for fname, reason in sorted(unsure_records):
        f.write(f"File  : {fname}\n")
        f.write(f"Reason: {reason}\n")
        f.write("\n")


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
