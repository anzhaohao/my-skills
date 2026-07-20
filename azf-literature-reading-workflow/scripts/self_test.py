from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    runtime = Path(__file__).resolve().parent / "runtime"
    sys.path.insert(0, str(runtime))
    from workflow.cli import build_parser

    required = {
        "locate",
        "confirm-locations",
        "doctor",
        "ingest-paper",
        "parse-with-mineru",
        "extract-highres-figures",
        "layout-sanity-check",
        "generate-zh-fulltext",
        "optimize-translation-footnotes",
        "generate-deep-reading",
        "migrate-concept-cards",
        "plan-batch",
        "validate-pilot",
    }
    parser = build_parser()
    subcommands = set()
    for action in parser._actions:
        choices = getattr(action, "choices", None)
        if isinstance(choices, dict):
            subcommands.update(choices)
    missing = sorted(required - subcommands)
    required_files = [
        runtime / "workflow" / "config" / "defaults.yaml",
        runtime / "workflow" / "config" / "path_policy.yaml",
        runtime / "workflow" / "config" / "locations.example.yaml",
        runtime / "workflow" / "templates" / "paper-workspace" / "中译.md",
        runtime / "runtime-version.json",
    ]
    missing_files = [str(path) for path in required_files if not path.is_file()]
    result = {
        "status": "pass" if not missing and not missing_files else "fail",
        "runtime": str(runtime),
        "subcommands": sorted(subcommands),
        "missing_subcommands": missing,
        "missing_files": missing_files,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())