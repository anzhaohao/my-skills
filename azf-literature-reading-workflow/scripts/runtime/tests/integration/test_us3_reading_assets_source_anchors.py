import json
from pathlib import Path

from workflow.models.source_anchor import SourceAnchor
from workflow.services.source_anchor_registry import SourceAnchorRegistry
from workflow.validators.source_anchors import validate_source_anchor_file


def test_source_anchor_registry_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "source-anchors.json"
    registry = SourceAnchorRegistry(path)
    registry.add(SourceAnchor(anchor_id="a1", paper_workspace="paper", source_type="pdf_page", page=1, note_target="note.md"))
    registry.save()
    assert json.loads(path.read_text(encoding="utf-8"))[0]["anchor_id"] == "a1"
    assert validate_source_anchor_file(path) == []

