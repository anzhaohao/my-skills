from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from workflow.adapters.figure_render_extractor import figure_skill_status
from workflow.adapters.mineru_docker import docker_status, mineru_image_available
from workflow.services.location_resolution import load_manifest, validate_manifest


def run(args) -> int:
    location_status = {
        "manifest": str(Path(args.location_manifest).expanduser().resolve()),
        "exists": False,
        "confirmed": False,
        "valid": False,
        "locations": {},
        "error": None,
    }
    manifest_path = Path(args.location_manifest).expanduser().resolve()
    if manifest_path.is_file():
        location_status["exists"] = True
        try:
            manifest = load_manifest(manifest_path)
            locations = validate_manifest(manifest, require_confirmed=False)
            location_status["confirmed"] = manifest.get("status") == "confirmed"
            location_status["valid"] = True
            location_status["locations"] = {name: str(path) for name, path in locations.items()}
        except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
            location_status["error"] = str(exc)

    manifest_vault = location_status["locations"].get("vault_root")
    vault = Path(manifest_vault or args.vault_root).resolve() if (manifest_vault or args.vault_root) else None
    status = {
        "locations": location_status,
        "vault": {"path": str(vault) if vault else None, "exists": vault.exists() if vault else False},
        "docker": docker_status(),
        "mineru": {"image": args.mineru_image, "image_available": mineru_image_available(args.mineru_image)},
        "skills": {
            "pdf_figure_render_extractor": Path("C:/Users/anzhaofeng/.skills-manager/skills/pdf-figure-render-extractor/SKILL.md").exists(),
            "pdf_figure_render_extractor_script": figure_skill_status(),
            "opencv_cv2": importlib.util.find_spec("cv2") is not None,
            "azf_paper_zh_reading_translator": Path("C:/Users/anzhaofeng/.skills-manager/skills/azf-paper-zh-reading-translator/SKILL.md").exists(),
        },
    }
    status["ready_for_reuse"] = all([
        status["locations"]["valid"],
        status["locations"]["confirmed"],
        status["vault"]["exists"],
        status["skills"]["pdf_figure_render_extractor"],
        status["skills"]["pdf_figure_render_extractor_script"]["available"],
        status["skills"]["azf_paper_zh_reading_translator"],
    ])
    status["ready_for_new_parse"] = all([
        status["ready_for_reuse"],
        status["docker"]["available"],
        status["mineru"]["image_available"],
    ])
    print(json.dumps(status, ensure_ascii=False, indent=2))
    if args.strict:
        ready = status["ready_for_reuse"] if args.reuse_existing else status["ready_for_new_parse"]
        return 0 if ready else 2
    return 0 if status["vault"]["exists"] else 1