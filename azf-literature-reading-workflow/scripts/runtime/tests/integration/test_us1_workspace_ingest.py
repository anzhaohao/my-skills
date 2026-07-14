from pathlib import Path

from workflow.models.paper import PaperSource
from workflow.services.paper_workspace import create_or_update_workspace
from workflow.validators.workspace_contract import validate_workspace_contract


def test_ingest_creates_workspace_without_overwrite(tmp_path: Path) -> None:
    pdf = tmp_path / "paper.pdf"
    pdf.write_bytes(b"%PDF-1.4\n")
    source = PaperSource(
        title_en="Paper",
        title_zh="测试论文",
        zotero_key="ABCD1234",
        zotero_pdf_attachment_key="PDF12345",
        pdf_attachments=[pdf],
    )
    workspace, _ = create_or_update_workspace(tmp_path / "Paper - 测试论文", pdf, source, dry_run=False)
    assert validate_workspace_contract(workspace.root_path) == []
    overview = workspace.overview_note.read_text(encoding="utf-8")
    assert 'Zotero PDF链接: "zotero://open-pdf/library/items/PDF12345"' in overview
    assert "Zotero条目链接" not in overview
    assert "[打开PDF](zotero://open-pdf/library/items/PDF12345)" in overview
    for role in ["中译", "精读", "图表", "问答"]:
        content = workspace.reading_note_path(role, "测试论文").read_text(encoding="utf-8")
        assert 'Zotero PDF链接: "zotero://open-pdf/library/items/PDF12345"' in content
    manual = workspace.reading_workspace_path / "人工.md"
    manual.write_text("human", encoding="utf-8")
    create_or_update_workspace(workspace.root_path, pdf, source, dry_run=False)
    assert manual.read_text(encoding="utf-8") == "human"
