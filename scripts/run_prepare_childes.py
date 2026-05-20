#!/usr/bin/env python3
"""
Uso:
    python3 run_prepare_childes.py

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

# Llama la función desde el el script
sys.path.insert(0, str(PYCHILDES))
from prepare_childes import process_cha_file  

# ── filtro CHI ────────────────────────────────────────────────────────────

def filter_chi_only(file_path: Path) -> int:
    """
    Filtra las líneas para quedarse sólo con las líneas que empiezan con <CHI>.
    Remeuve texto no verbal y <unk> que es resultado de palabras o señales no identificadas.
    Limpia líneas que no tienen contenido linguístico.
    """
  # Busca los archivos que ya fueron procesados por PyCHildes
    with open(file_path, encoding="utf-8") as f:
        lines = f.readlines()
  # Busca líneas con CHI
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

# ── Batch  ───────────────────────────────────────────────────────────────

#Mínimo de líneas que necesita un archivo para no ser descartado
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
      # Crea prepared_bi/control/ y prepared_bi/experimental/
        src_dir  = SRC_ROOT / group
        dst_dir  = DST_ROOT / group
        dst_dir.mkdir(parents=True, exist_ok=True)

      # Determina las convenciones de nombre que se le pondrá a los archivos
        prefix     = GROUP_PREFIX[group]
        cha_files  = sorted(src_dir.glob("*.cha"))
        file_id    = 0   # counter for the clean sequential ID

        print(f"\n[{group}] {len(cha_files)} files → {dst_dir}")
       
     
      # Se crea un loop y le aplica el preprocesamiento determinado por el script de PyChildes
      # Utiliza la configuración determinada por el yaml
      
        for idx, src_file in enumerate(cha_files, 1):
            tmp_file = dst_dir / (src_file.stem + OUTPUT_EXT)

            try:
                process_cha_file(str(src_file), str(tmp_file), config_path)
            # Aplica los filtros post PyChildes (Solo CHI, sin 0 y sin archivos con menos de 10 filas)
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
                # Si el archivo pasa los filtros llega aquí y recibe su nuevo nombre co id y grupo
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

    # ── REsumen final y lo que se pudo procesar ────────────────────────────────────────────────────────────────
    print(f"\nDone.")
    print(f"  Processed successfully : {total_ok}")
    print(f"  Skipped (no CHI speech): {total_empty}")
    print(f"  Skipped (< {MIN_LINES} lines)  : {total_short}")
    print(f"  Errors                 : {total_err}")
    print(f"  Output                 : {DST_ROOT}")

    # Se crea el log si surgen errores en el procesamiento
    if errors:
        err_log = DST_ROOT / "errors.log"
        with open(err_log, "w", encoding="utf-8") as f:
            for path, msg in errors:
                f.write(f"{path}\n  {msg}\n\n")
        print(f"  Error log              : {err_log}")


# ── Entry point ────────────────────────────────────────────────────────────────

  # Permite cargar el script para usar sus funciones
  if __name__ == "__main__":
      run_batch(DEFAULT_CFG, True)

