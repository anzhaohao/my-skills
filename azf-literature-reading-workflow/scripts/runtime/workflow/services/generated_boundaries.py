from __future__ import annotations

START = "<!-- BEGIN-GENERATED:workflow -->"
END = "<!-- END-GENERATED:workflow -->"


def wrap_generated(content: str) -> str:
    return f"{START}\n{content.rstrip()}\n{END}\n"


def has_generated_block(existing: str) -> bool:
    return START in existing and END in existing and existing.index(START) < existing.index(END)


def replace_generated_block(existing: str, generated: str) -> str:
    wrapped = wrap_generated(generated)
    if not has_generated_block(existing):
        normalized = existing.lstrip("\ufeff")
        if normalized.startswith("---") and normalized.count("---") >= 2:
            frontmatter = normalized.split("---", 2)[1]
            body = normalized.split("---", 2)[2].lstrip()
            tail = f"\n{body.rstrip()}\n" if body.strip() else ""
            return f"---{frontmatter}---\n\n{wrapped}{tail}"
        return f"{wrapped}\n{existing.rstrip()}\n" if existing.strip() else wrapped
    before = existing[: existing.index(START)]
    after = existing[existing.index(END) + len(END) :]
    return f"{before}{wrapped}{after.lstrip()}"


def manual_tail_template() -> str:
    return "\n## 人工笔记\n\n这里是用户手写区域，自动更新不得覆盖。\n"
