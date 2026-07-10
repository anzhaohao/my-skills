from __future__ import annotations

import json
from pathlib import Path

from workflow.adapters.zotero_obsidian_mcp import paper_source_from_pdf
from workflow.services.paper_workspace import create_or_update_workspace


def run(args) -> int:
    pdf_path = Path(args.pdf).resolve()
    workspace = Path(args.workspace).resolve() if args.workspace else pdf_path.parent.parent.resolve()
    source = paper_source_from_pdf(
        pdf_path,
        title_zh=args.title_zh,
        title_en=args.title_en,
        authors=args.author or [],
        year=args.year,
        venue=args.venue,
        doi=args.doi,
        citekey=args.citekey,
        zotero_key=args.zotero_key,
    )
    paper_workspace, plan = create_or_update_workspace(workspace, pdf_path, source, dry_run=args.dry_run)
    payload = {"workspace": str(paper_workspace.root_path), "plan": plan.to_dict()}
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0