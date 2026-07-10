from __future__ import annotations

import json

from workflow.services.location_resolution import confirm_manifest, default_manifest_path


def run(args) -> int:
    try:
        data = confirm_manifest(args.manifest or default_manifest_path(), args.registry)
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "fail", "reason": str(exc)}, ensure_ascii=False, indent=2))
        return 2
    print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0