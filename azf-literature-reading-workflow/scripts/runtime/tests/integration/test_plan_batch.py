from pathlib import Path

from workflow.commands.plan_batch import inspect_workspace
from workflow.models.paper import PaperWorkspace


def test_batch_plan_reuses_existing_mineru_without_docker(tmp_path: Path) -> None:
    workspace = tmp_path / "paper"
    source = workspace / "附件" / "原文"
    source.mkdir(parents=True)
    (source / "原文.pdf").write_bytes(b"pdf")
    (source / "MinerU英文全文.md").write_text("Source sentence.", encoding="utf-8")
    paper = PaperWorkspace.from_root(workspace)
    paper.quality_path.parent.mkdir(parents=True, exist_ok=True)
    paper.quality_path.write_text('{"layout_sanity_status":"pass","overall_status":"fail"}', encoding="utf-8")
    reading = workspace / "阅读工作台"
    reading.mkdir()
    (reading / "【中译】测试.md").write_text("摘要。" * 100, encoding="utf-8")

    item = inspect_workspace(workspace)

    assert item["state"] == "ready"
    assert item["next_action"] == "retranslate_from_existing_mineru"
    assert item["reuse_mineru"] is True
    assert item["docker_required"] is False
