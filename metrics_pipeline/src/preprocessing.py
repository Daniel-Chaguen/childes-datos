from __future__ import annotations

import re


ANGLE_RE = re.compile(r"<[^>]+>")
BRACKET_RE = re.compile(r"\[[^\]]+\]")
TOKEN_RE = re.compile(r"[a-z]+(?:'[a-z]+)?", re.IGNORECASE)


def clean_utterance(text: str) -> str:
    text = ANGLE_RE.sub(" ", text)
    text = BRACKET_RE.sub(" ", text)
    text = text.replace("_", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def tokenize(text: str) -> list[str]:
    return [match.group(0).lower() for match in TOKEN_RE.finditer(text)]


def prepare_utterances(utterances: list[str]) -> list[str]:
    return [cleaned for utt in utterances if (cleaned := clean_utterance(utt))]


def prepare_tokens(utterances: list[str]) -> list[str]:
    tokens: list[str] = []
    for utterance in utterances:
        tokens.extend(tokenize(utterance))
    return tokens
