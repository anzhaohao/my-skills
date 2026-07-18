from __future__ import annotations

import json
from pathlib import Path

from workflow.adapters.zotero_obsidian_mcp import paper_source_from_pdf
from workflow.models.artifact import ArtifactRun
from workflow.services.artifact_runs import initialize_run, make_artifact_id
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
        zotero_pdf_attachment_key=args.zotero_pdf_key,
        source_language=args.source_language,
    )
    artifact_root = args.resolved_locations["artifact_root"] if not args.dry_run else Path(args.location_manifest).parent / "dry-run-output"
    artifact_id = args.artifact_id or make_artifact_id(source.doi, source.zotero_key)
    if args.dry_run:
        artifact = ArtifactRun(artifact_id, artifact_root / artifact_id, workspace)
    else:
        artifact = initialize_run(
            artifact_root,
            workspace,
            artifact_id=artifact_id,
            doi=source.doi,
            zotero_key=source.zotero_key,
            paper_root=args.resolved_locations["paper_root"],
        )
    paper_workspace, plan = create_or_update_workspace(workspace, pdf_path, source, artifact_run=artifact, dry_run=args.dry_run)
    payload = {"workspace": str(paper_workspace.root_path), "artifact_id": artifact_id, "plan": plan.to_dict()}
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0
