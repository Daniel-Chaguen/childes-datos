from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from config import DISORDER_CODES, GROUP_DIRS


@dataclass
class TranscriptRecord:
    file_path: Path
    file_name: str
    group: str
    disorder_code: str | None
    disorder_label: str
    text: str
    utterances: list[str]


def iter_transcript_paths() -> list[tuple[str, Path]]:
    paths: list[tuple[str, Path]] = []
    for group, folder in GROUP_DIRS.items():
        if not folder.exists():
            continue
        for path in sorted(folder.glob("*.txt")):
            paths.append((group, path))
    return paths


def extract_disorder_code(file_name: str) -> tuple[str | None, str]:
    stem = Path(file_name).stem
    parts = re.split(r"[_\-\s]+", stem.upper())
    known = [part for part in parts if part in DISORDER_CODES]
    if known:
        code = known[0]
        return code, DISORDER_CODES[code]

    return None, "unspecified"


def read_transcript(path: Path, group: str) -> TranscriptRecord:
    text = path.read_text(encoding="utf-8", errors="ignore")
    utterances = [line.strip() for line in text.splitlines() if line.strip()]
    disorder_code, disorder_label = extract_disorder_code(path.name)
    return TranscriptRecord(
        file_path=path,
        file_name=path.name,
        group=group,
        disorder_code=disorder_code,
        disorder_label=disorder_label,
        text=text,
        utterances=utterances,
    )


def load_transcripts() -> list[TranscriptRecord]:
    return [read_transcript(path, group) for group, path in iter_transcript_paths()]
