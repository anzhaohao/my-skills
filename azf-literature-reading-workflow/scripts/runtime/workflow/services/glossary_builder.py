from __future__ import annotations

import re
from pathlib import Path


TERM_RE = re.compile(r"\b(?:LLM|AI|ALife|agentic|substrate|interpretability|complexity|collective)s?\b", re.IGNORECASE)


def collect_key_terms(markdown_path: Path) -> list[str]:
    if not markdown_path.exists():
        return []
    terms = {match.group(0) for match in TERM_RE.finditer(markdown_path.read_text(encoding="utf-8", errors="replace"))}
    return sorted(terms, key=str.lower)

