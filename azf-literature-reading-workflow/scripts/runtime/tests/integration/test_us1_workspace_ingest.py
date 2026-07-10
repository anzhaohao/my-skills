from pathlib import Path

from workflow.models.paper import PaperSource
from workflow.services.paper_workspace import create_or_update_workspace
from workflow.validators.workspace_contract import validate_workspace_contract


def test_ingest_creates_workspace_without_overwrite(tmp_path: Path) -> None:
    pdf = tmp_path / "paper.pdf"
    pdf.write_bytes(b"%PDF-1.4\n")
    source = PaperSource(title_en="Paper", title_zh="测试论文", pdf_attachments=[pdf])
    workspace, _ = create_or_update_workspace(tmp_path / "Paper - 测试论文", pdf, source, dry_run=False)
    assert validate_workspace_contract(workspace.root_path) == []
    manual = workspace.reading_workspace_path / "人工.md"
    manual.write_text("human", encoding="utf-8")
    create_or_update_workspace(workspace.root_path, pdf, source, dry_run=False)
    assert manual.read_text(encoding="utf-8") == "human"

