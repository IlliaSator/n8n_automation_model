from __future__ import annotations

import re

WHITESPACE_RE = re.compile(r"\s+")
NON_ALNUM_RE = re.compile(r"[^a-z0-9\s]+")


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    normalized = value.lower()
    normalized = NON_ALNUM_RE.sub(" ", normalized)
    normalized = WHITESPACE_RE.sub(" ", normalized)
    return normalized.strip()
