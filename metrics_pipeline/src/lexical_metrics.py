from __future__ import annotations

from collections import Counter
from math import sqrt


def safe_divide(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0


def moving_average_ttr(tokens: list[str], window_size: int = 50) -> float:
    if not tokens:
        return 0.0
    if len(tokens) <= window_size:
        return safe_divide(len(set(tokens)), len(tokens))

    scores = []
    for start in range(0, len(tokens) - window_size + 1):
        window = tokens[start:start + window_size]
        scores.append(len(set(window)) / window_size)
    return sum(scores) / len(scores)


def mtld(tokens: list[str], threshold: float = 0.72) -> float:
    if not tokens:
        return 0.0

    def factors(sequence: list[str]) -> float:
        types = set()
        token_count = 0
        factor_count = 0.0
        for token in sequence:
            token_count += 1
            types.add(token)
            current_ttr = len(types) / token_count
            if current_ttr <= threshold:
                factor_count += 1
                types = set()
                token_count = 0
        if token_count:
            excess = (1 - len(types) / token_count) / (1 - threshold)
            factor_count += excess
        return len(sequence) / factor_count if factor_count else 0.0

    forward = factors(tokens)
    backward = factors(list(reversed(tokens)))
    return (forward + backward) / 2 if forward and backward else max(forward, backward)


def lexical_metrics(tokens: list[str], common_words: set[str], mattr_window: int) -> dict[str, float | int]:
    counts = Counter(tokens)
    n_tokens = len(tokens)
    n_types = len(counts)
    hapax = sum(1 for value in counts.values() if value == 1)
    common_token_count = sum(value for word, value in counts.items() if word in common_words)

    return {
        "n_tokens": n_tokens,
        "n_types": n_types,
        "type_token_ratio": safe_divide(n_types, n_tokens),
        "moving_average_ttr": moving_average_ttr(tokens, mattr_window),
        "mtld": mtld(tokens),
        "unique_words": n_types,
        "hapax_legomena": hapax,
        "hapax_ratio": safe_divide(hapax, n_types),
        "common_word_token_count": common_token_count,
        "common_word_ratio": safe_divide(common_token_count, n_tokens),
        "lexical_density_sqrt": safe_divide(n_types, sqrt(n_tokens)) if n_tokens else 0.0,
    }
