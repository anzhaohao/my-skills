from pathlib import Path
from types import SimpleNamespace

from workflow.commands.parse_with_mineru import run as run_parse
from workflow.models.paper import PaperSource, PaperWorkspace
from workflow.services.artifact_runs import workspace_with_artifacts
from workflow.services.paper_workspace import create_or_update_workspace
from workflow.validators.workspace_contract import validate_workspace_contract


def test_chinese_source_merges_mineru_into_chinese_fulltext(tmp_path: Path) -> None:
    pdf = tmp_path / "paper.pdf"
    pdf.write_bytes(b"%PDF-1.4\n")
    artifact_root = tmp_path / "artifacts"
    workspace_root = tmp_path / "Chinese - 中文论文"
    source = PaperSource(
        title_en="Chinese Paper",
        title_zh="中文论文",
        source_language="zh",
        zotero_key="ABCD1234",
        zotero_pdf_attachment_key="PDF12345",
    )
    create_or_update_workspace(
        workspace_root,
        pdf,
        source,
        dry_run=False,
        artifact_root=artifact_root,
    )
    mineru = tmp_path / "mineru.md"
    mineru.write_text("# 摘要\n\n" + "这是中文论文正文。" * 80, encoding="utf-8")
    raw = tmp_path / "paper_middle.json"
    raw.write_text('{"pages": []}\n', encoding="utf-8")

    code = run_parse(
        SimpleNamespace(
            workspace=str(workspace_root),
            resolved_locations={"artifact_root": str(artifact_root)},
            pdf=None,
            mode="reuse",
            reuse_markdown=str(mineru),
            reuse_raw_output=str(raw),
            docker_image="mineru:4.0.2-vllm0.21.0",
            allow_preview=False,
        )
    )

    assert code == 0
    workspace = workspace_with_artifacts(workspace_root, artifact_root)
    chinese = workspace.chinese_fulltext_path()
    assert chinese.name == "【中译】中文论文.md"
    content = chinese.read_text(encoding="utf-8")
    assert "MinerU合并到中文正文: true" in content
    assert "这是中文论文正文" in content
    assert not workspace.mineru_source_path().exists()
    assert workspace.source_pdf_path().name == "【原文】中文论文.pdf"
    assert not (workspace_root / "附件" / "状态").exists()
    assert any(workspace.state_path.parent.joinpath("parser").glob("reused-middle-*.json"))
    assert validate_workspace_contract(workspace_root) == []
