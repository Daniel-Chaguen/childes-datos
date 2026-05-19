from __future__ import annotations

from collections import Counter
from statistics import mean

from lexical_metrics import safe_divide
from preprocessing import tokenize


def discourse_metrics(utterances: list[str], tokens: list[str]) -> dict[str, float | int]:
    normalized_utterances = [" ".join(tokenize(utterance)) for utterance in utterances]
    normalized_utterances = [utt for utt in normalized_utterances if utt]
    utterance_counts = Counter(normalized_utterances)
    token_counts = Counter(tokens)

    repeated_utterances = sum(count - 1 for count in utterance_counts.values() if count > 1)
    repeated_tokens = sum(count - 1 for count in token_counts.values() if count > 1)

    bigrams = list(zip(tokens, tokens[1:]))
    unique_bigrams = set(bigrams)

    lengths = [len(tokenize(utterance)) for utterance in utterances if tokenize(utterance)]
    length_changes = [
        abs(lengths[index] - lengths[index + 1])
        for index in range(len(lengths) - 1)
    ]

    return {
        "unique_utterance_count": len(utterance_counts),
        "unique_utterance_ratio": safe_divide(len(utterance_counts), len(normalized_utterances)),
        "repeated_utterance_count": repeated_utterances,
        "repeated_utterance_ratio": safe_divide(repeated_utterances, len(normalized_utterances)),
        "repeated_token_ratio": safe_divide(repeated_tokens, len(tokens)),
        "bigram_diversity": safe_divide(len(unique_bigrams), len(bigrams)),
        "mean_adjacent_length_change": mean(length_changes) if length_changes else 0.0,
    }
