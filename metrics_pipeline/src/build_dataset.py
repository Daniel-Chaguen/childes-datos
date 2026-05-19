from __future__ import annotations

import argparse
import sys
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

from config import (
    COMMON_WORD_MIN_CORPUS_FREQ,
    COMMON_WORD_MIN_DOC_FREQ_RATIO,
    CSV_OUTPUT,
    MATTR_WINDOW,
    OUTPUT_DIR,
    SPACY_MODEL,
    XLSX_OUTPUT,
)
from discourse_metrics import discourse_metrics
from io_utils import TranscriptRecord, load_transcripts
from lexical_metrics import lexical_metrics
from preprocessing import prepare_tokens, prepare_utterances
from semantic_metrics import semantic_metrics
from sentiment_metrics import sentiment_metrics
from syntactic_metrics import syntactic_metrics


def load_spacy_model():
    try:
        import spacy
    except ImportError as exc:
        raise RuntimeError(
            "spaCy is not installed. Install dependencies with: pip install -r requirements.txt"
        ) from exc

    try:
        return spacy.load(SPACY_MODEL)
    except OSError as exc:
        raise RuntimeError(
            f"spaCy model '{SPACY_MODEL}' is not installed. Run: python -m spacy download {SPACY_MODEL}"
        ) from exc


def build_common_words(records: list[TranscriptRecord]) -> set[str]:
    corpus_counts: Counter[str] = Counter()
    doc_freq: defaultdict[str, int] = defaultdict(int)

    for record in records:
        utterances = prepare_utterances(record.utterances)
        tokens = prepare_tokens(utterances)
        corpus_counts.update(tokens)
        for token in set(tokens):
            doc_freq[token] += 1

    min_doc_freq = max(2, int(len(records) * COMMON_WORD_MIN_DOC_FREQ_RATIO))
    return {
        word for word, count in corpus_counts.items()
        if count >= COMMON_WORD_MIN_CORPUS_FREQ and doc_freq[word] >= min_doc_freq
    }


def process_record(record: TranscriptRecord, common_words: set[str], nlp=None) -> dict:
    utterances = prepare_utterances(record.utterances)
    tokens = prepare_tokens(utterances)
    docs = list(nlp.pipe(utterances)) if nlp is not None and utterances else None

    row = {
        "file_name": record.file_name,
        "file_path": str(record.file_path),
        "group": record.group,
        "disorder_code": record.disorder_code,
        "disorder_label": record.disorder_label,
        "raw_character_count": len(record.text),
    }
    row.update(lexical_metrics(tokens, common_words, MATTR_WINDOW))
    row.update(syntactic_metrics(utterances, docs))
    row.update(semantic_metrics(utterances, docs))
    row.update(sentiment_metrics(tokens))
    row.update(discourse_metrics(utterances, tokens))
    return row


def build_dataset(use_spacy: bool = True, limit: int | None = None) -> pd.DataFrame:
    records = load_transcripts()
    if limit:
        records = records[:limit]

    common_words = build_common_words(records)
    nlp = load_spacy_model() if use_spacy else None

    rows = []
    total = len(records)
    for index, record in enumerate(records, start=1):
        rows.append(process_record(record, common_words, nlp))
        if index % 250 == 0 or index == total:
            print(f"Processed {index}/{total} files", flush=True)

    return pd.DataFrame(rows)


def save_outputs(df: pd.DataFrame) -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    df.to_csv(CSV_OUTPUT, index=False, encoding="utf-8")
    df.to_excel(XLSX_OUTPUT, index=False)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-spacy", action="store_true", help="Skip POS/dependency/vector metrics.")
    parser.add_argument("--limit", type=int, default=None, help="Process only the first N files for testing.")
    args = parser.parse_args(argv)

    df = build_dataset(use_spacy=not args.no_spacy, limit=args.limit)
    save_outputs(df)
    print(f"Saved {len(df)} rows to {CSV_OUTPUT}")
    print(f"Saved {len(df)} rows to {XLSX_OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
