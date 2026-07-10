from pathlib import Path

from workflow.services.template_review import build_template_review


def test_template_review_mentions_workspace_sections(tmp_path: Path) -> None:
    review = build_template_review(tmp_path / "Paper")
    assert "阅读工作台" in review
    assert "附件/图片" in review

