from __future__ import annotations

from pathlib import Path


def build_template_review(workspace_root: Path) -> str:
    return f"""# Starter Structure Review

- Workspace: `{workspace_root}`
- Check `阅读工作台/总览.md` for navigation.
- Check generated/manual boundaries before regeneration.
- Check `附件/原文/` and `附件/图片/` stay inside the paper folder.
"""

