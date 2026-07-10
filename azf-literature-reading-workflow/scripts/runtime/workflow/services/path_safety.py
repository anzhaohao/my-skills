from __future__ import annotations

import re
from pathlib import Path

WINDOWS_RESERVED = {name.upper() for name in ["CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))]}
UNSAFE_CHARS = r'<>:"/\\|?*'


def sanitize_filename(value: str, fallback: str = "untitled") -> str:
    cleaned = "".join("_" if char in UNSAFE_CHARS else char for char in value)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" .")
    if not cleaned:
        cleaned = fallback
    if cleaned.upper() in WINDOWS_RESERVED:
        cleaned = f"{cleaned}_"
    return cleaned[:160]


def resolve_path(path: str | Path) -> Path:
    return Path(path).expanduser().resolve()


def ensure_under_root(path: str | Path, allowed_root: str | Path) -> Path:
    resolved = resolve_path(path)
    root = resolve_path(allowed_root)
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"Path {resolved} is outside allowed root {root}") from exc
    return resolved


def is_under_any_root(path: str | Path, roots: list[str | Path]) -> bool:
    resolved = resolve_path(path)
    for root in roots:
        try:
            resolved.relative_to(resolve_path(root))
            return True
        except ValueError:
            continue
    return False


def relative_markdown_link(from_note: Path, target: Path) -> str:
    rel = target.resolve().relative_to(from_note.resolve().parent) if False else None
    try:
        rel_path = target.resolve().relative_to(from_note.resolve().parent)
    except ValueError:
        rel_path = Path(*Path(__import__("os").path.relpath(target.resolve(), from_note.resolve().parent)).parts)
    return rel_path.as_posix()

