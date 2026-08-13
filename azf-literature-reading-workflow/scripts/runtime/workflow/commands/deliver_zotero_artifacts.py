from __future__ import annotations

import json
from pathlib import Path

from workflow.services.zotero_artifact_delivery import (
    DEFAULT_TOKEN_FILE,
    ZoteroArtifactDeliveryError,
    build_artifact_import_request,
    load_delivery_token,
    post_artifact_import_request,
    retire_delivered_workspace,
    retirement_target,
)


def run(args) -> int:
    locations = getattr(args, "resolved_locations", {}) or {}
    try:
        payload = build_artifact_import_request(
            Path(args.workspace),
            Path(locations["artifact_root"]),
            library_id=args.library_id,
        )
        if not args.apply:
            print(
                json.dumps(
                    {
                        "status": "dry-run",
                        "endpoint": args.endpoint,
                        "request": payload,
                        "retireWorkspace": bool(args.retire_workspace),
                        "retirementTarget": str(
                            retirement_target(
                                Path(args.workspace),
                                Path(locations["artifact_root"]),
                                str(payload["workflowRunID"]),
                            )
                        )
                        if args.retire_workspace
                        else None,
                        "note": "未向 Zotero 发送请求；确认后增加 --apply。",
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 0
        token = load_delivery_token(
            environment_name=args.token_env,
            token_file=Path(args.token_file or DEFAULT_TOKEN_FILE),
        )
        response = post_artifact_import_request(
            args.endpoint,
            token,
            payload,
            timeout=args.timeout,
        )
        retired_workspace = None
        if args.retire_workspace:
            retired_workspace = retire_delivered_workspace(
                Path(args.workspace),
                Path(locations["artifact_root"]),
                payload,
                response,
            )
    except (KeyError, OSError, ValueError, ZoteroArtifactDeliveryError) as exc:
        print(json.dumps({"status": "fail", "reason": str(exc)}, ensure_ascii=False, indent=2))
        return 2
    print(
        json.dumps(
            {
                "status": "pass",
                "endpoint": args.endpoint,
                "parentItemKey": payload["parentItemKey"],
                "workflowRunID": payload["workflowRunID"],
                "response": response,
                "retiredWorkspace": str(retired_workspace) if retired_workspace else None,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0
