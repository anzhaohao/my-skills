from argparse import Namespace
from pathlib import Path

from workflow.commands.generate_zh_fulltext import run as generate_fulltext
from workflow.models.artifact import ArtifactRun
from workflow.models.paper import PaperSource
from workflow.services.paper_workspace import create_or_update_workspace
from workflow.validators.translation_fidelity import validate_workspace_translation
from workflow.validators.workspace_contract import validate_workspace_contract
from workflow.validators.layout_sanity import simple_layout_sanity


def test_chinese_source_uses_original_note_and_no_translation_audit(tmp_path: Path) -> None:
    pdf = tmp_path / "paper.pdf"
    pdf.write_bytes(b"%PDF-1.4\n")
    source = PaperSource(
        title_en="Chinese Paper",
        title_zh="中文论文",
        zotero_key="ITEM1234",
        zotero_pdf_attachment_key="PDF12345",
        source_language="zh",
        pdf_attachments=[pdf],
    )
    workspace_root = tmp_path / "Chinese Paper - 中文论文"
    artifact = ArtifactRun("20260718_101754__10.1234_test", tmp_path / "output" / "20260718_101754__10.1234_test", workspace_root)
    workspace, _ = create_or_update_workspace(workspace_root, pdf, source, artifact_run=artifact, dry_run=False)
    overview = workspace.overview_note.read_text(encoding="utf-8")
    assert '原文语言: "zh"' in overview
    assert "中译适用: false" in overview
    assert '中文全文: "[[【原文】中文论文.md|中文原文]]"' in overview
    assert 'MinerU中文全文: "[[' in overview
    assert workspace.reading_note_path("原文", "中文论文").is_file()
    assert not workspace.reading_note_path("中译", "中文论文").exists()
    assert validate_workspace_contract(workspace.root_path) == []

    workspace.mineru_markdown_path.write_text("中文原文正文。" * 100, encoding="utf-8")
    result = generate_fulltext(Namespace(
        workspace=str(workspace.root_path),
        title_zh="中文论文",
        translated_note=None,
        translation_audit=None,
        dry_run=False,
        force=True,
        artifact_id=artifact.artifact_id,
        resolved_locations={"artifact_root": tmp_path / "output", "paper_root": tmp_path},
    ))
    assert result == 0
    assert validate_workspace_translation(workspace.root_path) == []
    assert not workspace.translation_audit_path.exists()


def test_layout_sanity_accepts_spaced_chinese_references_heading(tmp_path: Path) -> None:
    markdown = tmp_path / "MinerU中文全文.md"
    markdown.write_text(("正文内容完整且可读。\n" * 80) + "\n## 参 考 文 献\n\n[1] 参考条目。\n", encoding="utf-8")
    status, notes = simple_layout_sanity(markdown)
    assert status == "pass"
    assert notes == []
