from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


def write_run_manifest(workspace_root: Path, command: str, payload: dict) -> Path:
    reports_dir = workspace_root / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "command": command,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "payload": payload,
    }
    path = reports_dir / "run-manifest.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return path

