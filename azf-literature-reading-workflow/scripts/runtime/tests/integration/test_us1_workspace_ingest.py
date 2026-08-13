from pathlib import Path

from workflow.models.paper import PaperSource
from workflow.services.paper_workspace import create_or_update_workspace
from workflow.validators.workspace_contract import validate_workspace_contract


def test_ingest_creates_core_workspace_without_overwrite(tmp_path: Path) -> None:
    pdf = tmp_path / "paper.pdf"
    pdf.write_bytes(b"%PDF-1.4\n")
    artifact_root = tmp_path / "artifacts"
    source = PaperSource(
        title_en="Paper",
        title_zh="测试论文",
        zotero_key="ABCD1234",
        zotero_pdf_attachment_key="PDF12345",
        pdf_attachments=[pdf],
    )
    workspace, _ = create_or_update_workspace(
        tmp_path / "Paper - 测试论文",
        pdf,
        source,
        dry_run=False,
        artifact_root=artifact_root,
    )

    assert workspace.source_pdf_path("测试论文").name == "【原文】测试论文.pdf"
    assert workspace.source_pdf_path("测试论文").is_file()
    assert sorted(path.name for path in workspace.reading_workspace_path.glob("*.md")) == [
        "【中译】测试论文.md",
        "【总览】测试论文.md",
    ]
    assert not (workspace.root_path / "附件" / "状态").exists()
    assert workspace.state_path.parent.parent == artifact_root.resolve()
    assert workspace.state_path.is_dir()
    assert (workspace.state_path.parent / "parser").is_dir()
    assert (workspace.state_path.parent / "logs").is_dir()

    workspace.mineru_source_path("测试论文").write_text("Source sentence.", encoding="utf-8")
    assert validate_workspace_contract(workspace.root_path) == []
    overview = workspace.overview_note.read_text(encoding="utf-8")
    assert 'Zotero PDF链接: "zotero://open-pdf/library/items/PDF12345"' in overview
    assert '中文全文: "[[【中译】测试论文.md|中译笔记]]"' in overview
    assert '原文PDF: "[[【原文】测试论文.pdf|原文PDF]]"' in overview
    assert 'MinerU原文: "[[【MinerU原文】测试论文.md|MinerU原文]]"' in overview
    assert "[[附件/" not in overview
    assert "Zotero条目链接" not in overview
    assert "[打开PDF](zotero://open-pdf/library/items/PDF12345)" in overview
    for role in ["精读", "图表", "问答"]:
        assert not workspace.reading_note_path(role, "测试论文").exists()

    manual = workspace.reading_workspace_path / "人工.md"
    manual.write_text("human", encoding="utf-8")
    create_or_update_workspace(
        workspace.root_path,
        pdf,
        source,
        dry_run=False,
        artifact_root=artifact_root,
    )
    assert manual.read_text(encoding="utf-8") == "human"


def test_ingest_requires_external_artifact_root_for_writes(tmp_path: Path) -> None:
    pdf = tmp_path / "paper.pdf"
    pdf.write_bytes(b"%PDF-1.4\n")
    source = PaperSource(title_zh="测试论文")

    try:
        create_or_update_workspace(tmp_path / "Paper", pdf, source, dry_run=False)
    except ValueError as exc:
        assert "artifact_root" in str(exc)
    else:
        raise AssertionError("write-enabled ingest must reject vault-local state")
