from __future__ import annotations


POSITIVE_WORDS = {
    "good", "great", "happy", "love", "like", "nice", "yes", "yay", "fun",
    "play", "pretty", "cool", "best", "better", "thank", "thanks",
}

NEGATIVE_WORDS = {
    "bad", "sad", "mad", "angry", "cry", "hurt", "no", "not", "don't",
    "cant", "can't", "hate", "scared", "afraid", "wrong", "stop",
}


def sentiment_metrics(tokens: list[str]) -> dict[str, float | int]:
    positive = sum(1 for token in tokens if token in POSITIVE_WORDS)
    negative = sum(1 for token in tokens if token in NEGATIVE_WORDS)
    total = len(tokens)
    emotional = positive + negative
    polarity = (positive - negative) / emotional if emotional else 0.0
    return {
        "positive_word_count": positive,
        "negative_word_count": negative,
        "sentiment_polarity_lexicon": polarity,
        "emotional_word_ratio": emotional / total if total else 0.0,
    }
