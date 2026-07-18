from pathlib import Path

from workflow.models.artifact import ArtifactRun
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
    workspace_root = tmp_path / "Paper - 测试论文"
    artifact = ArtifactRun("20260718_101754__10.1234_test", tmp_path / "output" / "20260718_101754__10.1234_test", workspace_root)
    workspace, _ = create_or_update_workspace(workspace_root, pdf, source, artifact_run=artifact, dry_run=False)
    assert validate_workspace_contract(workspace.root_path) == []
    overview = workspace.overview_note.read_text(encoding="utf-8")
    assert 'Zotero PDF链接: "zotero://open-pdf/library/items/PDF12345"' in overview
    assert '原文语言: "en"' in overview
    assert "中译适用: true" in overview
    assert '中文全文: "[[' in overview
    assert '中文全文: "[[【中译】测试论文.md|中译笔记]]"' in overview
    assert "Zotero条目链接" not in overview
    assert "[打开PDF](zotero://open-pdf/library/items/PDF12345)" in overview
    for role in ["中译", "精读", "图表", "问答"]:
        content = workspace.reading_note_path(role, "测试论文").read_text(encoding="utf-8")
        assert 'Zotero PDF链接: "zotero://open-pdf/library/items/PDF12345"' in content
    manual = workspace.reading_workspace_path / "人工.md"
    manual.write_text("human", encoding="utf-8")
    create_or_update_workspace(workspace.root_path, pdf, source, artifact_run=artifact, dry_run=False)
    assert manual.read_text(encoding="utf-8") == "human"
