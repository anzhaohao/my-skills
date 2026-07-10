from __future__ import annotations

from pathlib import Path

from workflow.services.path_safety import sanitize_filename


def infer_title_from_pdf(pdf_path: Path) -> str:
    stem = pdf_path.stem
    if " - " in stem:
        parts = stem.split(" - ")
        if len(parts) >= 3:
            return " - ".join(parts[2:])
    return stem


def infer_year_from_name(name: str) -> str | None:
    for token in name.replace("-", " ").split():
        if token.isdigit() and len(token) == 4 and token.startswith(("19", "20")):
            return token
    return None


def select_english_anchor(title: str) -> str:
    lowered = title.lower()
    if "conversable complexity" in lowered:
        return "Conversable Complexity"
    if "agentic llm" in lowered:
        return "Agentic LLM Collectives"
    words = [word.strip(",:;()[]{}") for word in title.split()]
    meaningful = [word for word in words if len(word) > 3 and word.lower() not in {"with", "from", "into", "using", "paper"}]
    return " ".join(meaningful[:3]) if meaningful else "Paper"


def workspace_name_from_title(title_en: str, title_zh: str | None = None) -> str:
    anchor = select_english_anchor(title_en)
    zh = title_zh or "中文短题名待定"
    return sanitize_filename(f"{anchor} - {zh}")


def note_title_from_workspace(workspace_root: Path) -> str:
    return workspace_root.name

