from __future__ import annotations

import json
from pathlib import Path

from workflow.services.location_resolution import (
    default_manifest_path,
    default_registry_path,
    resolve_locations,
    write_pending_manifest,
)


def run(args) -> int:
    registry = Path(args.registry).expanduser().resolve() if args.registry else default_registry_path()
    manifest = Path(args.manifest).expanduser().resolve() if args.manifest else default_manifest_path()
    resolution = resolve_locations(
        vault_root=args.vault_root,
        paper_root=args.paper_root,
        concept_library_root=args.concept_library_root,
        template_path=args.template_path,
        registry_path=registry,
    )
    manifest_path = write_pending_manifest(resolution, manifest, registry)
    payload = resolution.to_manifest(registry)
    payload["manifest_path"] = str(manifest_path)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if resolution.ready_for_confirmation else 2