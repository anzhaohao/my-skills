import json
from pathlib import Path

from workflow.models.paper import PaperWorkspace
from workflow.services.workspace_paths import repair_generated_json, resolve_workspace_path
from workflow.validators.workspace_cleanliness import validate_workspace_cleanliness


def test_repair_generated_paths_after_workspace_move(tmp_path: Path) -> None:
    workspace = PaperWorkspace.from_root(tmp_path / "Paper")
    workspace.figure_path.mkdir(parents=True)
    workspace.state_path.mkdir(parents=True)
    figure = workspace.figure_path / "Fig-01.png"
    figure.write_bytes(b"png")
    manifest = [{
        "asset_id": "fig-1",
        "file_path": "E:/old/vault/0_论文精读/Paper/附件/图片/Fig-01.png",
        "source_pdf": "E:/old/vault/0_论文精读/Paper/附件/原文/原文.pdf",
        "page": 1,
        "crop_status": "success",
        "accepted_as_highres_figure": True,
    }]
    workspace.figure_manifest_path.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")

    report = repair_generated_json(workspace.figure_manifest_path, workspace.root_path, apply=True)
    assert report["changed_paths"] == 2
    repaired = json.loads(workspace.figure_manifest_path.read_text(encoding="utf-8"))
    assert repaired[0]["file_path"] == "附件/图片/Fig-01.png"
    assert resolve_workspace_path(workspace.root_path, repaired[0]["file_path"]) == figure.resolve()
    cleanliness_issues = validate_workspace_cleanliness(workspace.root_path)
    assert any("machine JSON retained" in issue for issue in cleanliness_issues)
