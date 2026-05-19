from __future__ import annotations

from statistics import mean, pstdev

from config import POS_TAGS
from lexical_metrics import safe_divide
from preprocessing import tokenize


def dependency_depth(token) -> int:
    children = list(token.children)
    if not children:
        return 1
    return 1 + max(dependency_depth(child) for child in children)


def syntactic_metrics(utterances: list[str], docs: list | None = None) -> dict[str, float | int]:
    token_lengths = [len(tokenize(utterance)) for utterance in utterances]
    valid_lengths = [length for length in token_lengths if length > 0]
    total_tokens = sum(valid_lengths)

    metrics: dict[str, float | int] = {
        "n_utterances": len(utterances),
        "n_nonempty_utterances": len(valid_lengths),
        "mean_utterance_length": mean(valid_lengths) if valid_lengths else 0.0,
        "sd_utterance_length": pstdev(valid_lengths) if len(valid_lengths) > 1 else 0.0,
        "min_utterance_length": min(valid_lengths) if valid_lengths else 0,
        "max_utterance_length": max(valid_lengths) if valid_lengths else 0,
        "one_word_utterance_ratio": safe_divide(sum(1 for length in valid_lengths if length == 1), len(valid_lengths)),
        "short_utterance_ratio_1_to_3": safe_divide(sum(1 for length in valid_lengths if 1 <= length <= 3), len(valid_lengths)),
    }

    for tag in POS_TAGS:
        metrics[f"pos_{tag.lower()}_ratio"] = 0.0

    if not docs:
        metrics["syntactic_tree_depth_mean"] = 0.0
        metrics["syntactic_tree_depth_max"] = 0
        metrics["spacy_parsed_utterances"] = 0
        return metrics

    pos_counts = {tag: 0 for tag in POS_TAGS}
    depths: list[int] = []
    parsed_utterances = 0
    for doc in docs:
        lexical_tokens = [token for token in doc if not token.is_punct and not token.is_space]
        if not lexical_tokens:
            continue
        parsed_utterances += 1
        for token in lexical_tokens:
            if token.pos_ in pos_counts:
                pos_counts[token.pos_] += 1
        roots = [token for token in lexical_tokens if token.dep_ == "ROOT"]
        if roots:
            depths.append(max(dependency_depth(root) for root in roots))

    for tag, count in pos_counts.items():
        metrics[f"pos_{tag.lower()}_ratio"] = safe_divide(count, total_tokens)

    metrics["syntactic_tree_depth_mean"] = mean(depths) if depths else 0.0
    metrics["syntactic_tree_depth_max"] = max(depths) if depths else 0
    metrics["spacy_parsed_utterances"] = parsed_utterances
    return metrics
