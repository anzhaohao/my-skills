import json
from pathlib import Path

from workflow.services.figure_manifest import manifest_issues


def test_figure_manifest_validates_file_presence(tmp_path: Path) -> None:
    image = tmp_path / "Fig-01.png"
    image.write_bytes(b"png")
    manifest = tmp_path / "figure_extraction_manifest.json"
    manifest.write_text(
        json.dumps(
            [
                {
                    "asset_id": "fig-01",
                    "file_path": str(image),
                    "source_pdf": str(tmp_path / "paper.pdf"),
                    "page": 1,
                    "crop_status": "needs_review",
                }
            ]
        ),
        encoding="utf-8",
    )
    assert manifest_issues(manifest) == []

