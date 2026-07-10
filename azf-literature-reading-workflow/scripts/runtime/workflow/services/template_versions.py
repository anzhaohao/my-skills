from __future__ import annotations

import yaml
from pathlib import Path


def load_template_version(template_yaml: Path) -> dict:
    if not template_yaml.exists():
        return {"version": "0.0.0", "status": "missing"}
    data = yaml.safe_load(template_yaml.read_text(encoding="utf-8")) or {}
    return data


def compatible_template(template_yaml: Path, expected_major: int = 1) -> bool:
    version = str(load_template_version(template_yaml).get("version", "0.0.0"))
    return version.split(".", 1)[0] == str(expected_major)

