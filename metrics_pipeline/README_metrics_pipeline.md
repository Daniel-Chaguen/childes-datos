# NLP Metrics Pipeline

This project builds one row per transcript file from `prepared_bi/control` and `prepared_bi/experimental`.

## Setup

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

## Run

Quick test:

```bash
python src/build_dataset.py --limit 50
```

Full run:

```bash
python src/build_dataset.py
```

Outputs:

- `outputs/metrics_by_file.csv`
- `outputs/metrics_by_file.xlsx`

## Embedding strategy

The lightweight default uses `spaCy` for syntax and POS tagging. Because `en_core_web_sm` does not include rich semantic vectors, the pipeline also calculates lightweight TF-IDF semantic coherence metrics:

- `tfidf_adjacent_coherence`: similarity between consecutive utterances.
- `tfidf_centroid_distance`: average distance from each utterance to the file-level semantic centroid.

If a larger spaCy model with vectors is used later, the `spacy_vector_*` columns will become informative too.

A heavier future option is `sentence-transformers`, for example `all-MiniLM-L6-v2` or `all-mpnet-base-v2`. These usually produce stronger sentence-level semantic coherence metrics, but require extra installation, more disk, and longer runtime.

Reminder: after the first exploratory analysis, reconsider whether transformer embeddings are worth adding.

## Notes

- Disorder codes are extracted from filename chunks when possible: `TD`, `DS`, `LT`, `HL`, `SLI`.
- Files without one of the currently known codes are marked `unspecified`.
- Add extra confirmed disorder codes to `DISORDER_CODES` in `src/config.py` before rerunning if you identify additional clinical labels.
- Common words are defined inside this corpus using corpus frequency and document frequency thresholds in `src/config.py`.
