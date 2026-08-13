from __future__ import annotations

import re
from pathlib import Path


WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")


def short_wikilink(path: Path, alias: str) -> str:
    """Render a vault-internal Wikilink using only the target filename."""
    return f"[[{path.name}|{alias}]]"


def wikilink_target(inner: str) -> str:
    return inner.split("|", 1)[0].strip()


def wikilink_targets(markdown: str) -> list[str]:
    return [wikilink_target(match.group(1)) for match in WIKILINK_RE.finditer(markdown)]


def path_qualified_wikilink_targets(markdown: str) -> list[str]:
    return [target for target in wikilink_targets(markdown) if "/" in target or "\\" in target]


def shorten_wikilink_targets(markdown: str) -> str:
    """Drop folder components from existing Wikilink targets, preserving anchors and aliases."""

    def replace(match: re.Match[str]) -> str:
        inner = match.group(1)
        target, separator, alias = inner.partition("|")
        if "/" not in target and "\\" not in target:
            return match.group(0)
        file_target, anchor_separator, anchor = target.partition("#")
        short_target = file_target.replace("\\", "/").rstrip("/").rsplit("/", 1)[-1]
        if anchor_separator:
            short_target += f"#{anchor}"
        suffix = f"|{alias}" if separator else ""
        return f"[[{short_target}{suffix}]]"

    return WIKILINK_RE.sub(replace, markdown)
