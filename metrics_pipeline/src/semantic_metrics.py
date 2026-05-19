from __future__ import annotations

from statistics import mean

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    denominator = np.linalg.norm(a) * np.linalg.norm(b)
    if denominator == 0:
        return 0.0
    return float(np.dot(a, b) / denominator)


def tfidf_semantic_metrics(utterances: list[str]) -> dict[str, float | int]:
    clean_utterances = [utterance for utterance in utterances if utterance.strip()]
    if len(clean_utterances) < 2:
        return {
            "tfidf_adjacent_coherence": 0.0,
            "tfidf_centroid_distance": 0.0,
            "tfidf_utterances": len(clean_utterances),
        }

    vectorizer = TfidfVectorizer(lowercase=True, token_pattern=r"(?u)\b[a-zA-Z][a-zA-Z']+\b")
    try:
        matrix = vectorizer.fit_transform(clean_utterances).toarray()
    except ValueError:
        return {
            "tfidf_adjacent_coherence": 0.0,
            "tfidf_centroid_distance": 0.0,
            "tfidf_utterances": len(clean_utterances),
        }

    adjacent = [
        cosine_similarity(matrix[index], matrix[index + 1])
        for index in range(matrix.shape[0] - 1)
    ]
    centroid = np.mean(matrix, axis=0)
    centroid_distances = [1 - cosine_similarity(vector, centroid) for vector in matrix]

    return {
        "tfidf_adjacent_coherence": mean(adjacent) if adjacent else 0.0,
        "tfidf_centroid_distance": mean(centroid_distances) if centroid_distances else 0.0,
        "tfidf_utterances": len(clean_utterances),
    }


def spacy_vector_metrics(docs: list | None = None) -> dict[str, float | int]:
    if not docs:
        return {
            "spacy_vector_adjacent_coherence": 0.0,
            "spacy_vector_centroid_distance": 0.0,
            "spacy_vector_norm_mean": 0.0,
            "spacy_docs_with_vectors": 0,
        }

    vectors = [doc.vector for doc in docs if getattr(doc, "has_vector", False) and doc.vector_norm > 0]
    if not vectors:
        return {
            "spacy_vector_adjacent_coherence": 0.0,
            "spacy_vector_centroid_distance": 0.0,
            "spacy_vector_norm_mean": 0.0,
            "spacy_docs_with_vectors": 0,
        }

    adjacent = [
        cosine_similarity(vectors[index], vectors[index + 1])
        for index in range(len(vectors) - 1)
    ]
    centroid = np.mean(vectors, axis=0)
    centroid_distances = [1 - cosine_similarity(vector, centroid) for vector in vectors]

    return {
        "spacy_vector_adjacent_coherence": mean(adjacent) if adjacent else 0.0,
        "spacy_vector_centroid_distance": mean(centroid_distances) if centroid_distances else 0.0,
        "spacy_vector_norm_mean": mean(float(np.linalg.norm(vector)) for vector in vectors),
        "spacy_docs_with_vectors": len(vectors),
    }


def semantic_metrics(utterances: list[str], docs: list | None = None) -> dict[str, float | int]:
    metrics = tfidf_semantic_metrics(utterances)
    metrics.update(spacy_vector_metrics(docs))
    return metrics
